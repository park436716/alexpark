"""Setup pattern library — each pattern has detect() + empirical forward odds.

Modest Proposal / Digital Analyst 프레임의 "Patterns":
    시장에 반복적으로 존재하는 set-up 을 정의하고, 각 set-up 이 만들어내는
    forward table-odds 를 실측(백테스트)해서 "이 셋업이 잡히면 다음 N일간
    승률 X% / 손익비 Y" 라는 확률테이블을 유지한다.

각 Pattern 은:
    - detect(row, hist) → PatternMatch(matched, strength, detail)
    - forward_window / tp / sl 파라미터로 forward odds 를 계산 가능
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class PatternMatch:
    matched: bool
    strength: float  # 0..1 — 조건 성립도 (여러 서브조건의 종합)
    detail: dict


@dataclass
class ForwardOdds:
    n: int
    hit_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float
    payoff: float


@dataclass
class Pattern:
    name: str
    description: str
    detect: Callable[[pd.Series, pd.DataFrame], PatternMatch]
    forward_window: int
    tp: float = 0.05
    sl: float = -0.03


def compute_forward_odds(df: pd.DataFrame, pattern: Pattern,
                         warmup: int = 60) -> ForwardOdds:
    """Walk history, count each match, compute forward N-day returns."""
    rets: list[float] = []
    n = len(df)
    for i in range(warmup, n - pattern.forward_window):
        row = df.iloc[i]
        hist = df.iloc[max(0, i - 60):i + 1]
        m = pattern.detect(row, hist)
        if not m.matched:
            continue
        entry = float(row["close"])
        exit_ret = None
        for j in range(1, pattern.forward_window + 1):
            fwd = df.iloc[i + j]
            if fwd["low"] / entry - 1 <= pattern.sl:
                exit_ret = pattern.sl
                break
            if fwd["high"] / entry - 1 >= pattern.tp:
                exit_ret = pattern.tp
                break
        if exit_ret is None:
            fwd = df.iloc[i + pattern.forward_window]
            exit_ret = float(fwd["close"]) / entry - 1
        rets.append(exit_ret)

    if not rets:
        return ForwardOdds(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    arr = np.array(rets)
    wins = arr[arr > 0]
    losses = arr[arr <= 0]
    hit_rate = len(wins) / len(arr)
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    expectancy = hit_rate * avg_win + (1 - hit_rate) * avg_loss
    payoff = abs(avg_win / avg_loss) if avg_loss < 0 else 0.0
    return ForwardOdds(len(arr), round(hit_rate, 3), round(avg_win, 4),
                       round(avg_loss, 4), round(expectancy, 4),
                       round(payoff, 2))


# ---- Pattern implementations ----

def _accumulation_breakout(row: pd.Series, hist: pd.DataFrame) -> PatternMatch:
    """5일 수급 매집 + 오늘 20일 신고가 브레이크아웃 + 거래량."""
    hi_20 = hist["high"].iloc[-21:-1].max() if len(hist) >= 21 else np.nan
    supply_5d = (row.get("foreign_ratio_5d") or 0) + (row.get("inst_ratio_5d") or 0)
    vol_ratio = float(row.get("vol_ratio") or 0)
    close_pos = float(row.get("close_pos") or 0)
    breakout = pd.notna(hi_20) and row["close"] > hi_20
    matched = bool(supply_5d >= 0.05 and vol_ratio >= 1.5 and breakout and close_pos >= 0.6)
    strength = float(np.clip(
        (supply_5d / 0.15) * 0.5
        + (min(vol_ratio, 3) / 3) * 0.3
        + close_pos * 0.2,
        0, 1))
    return PatternMatch(matched, strength, {
        "supply_5d": round(supply_5d, 4),
        "vol_ratio": round(vol_ratio, 2),
        "breakout_pct": round(row["close"] / hi_20 - 1, 4) if pd.notna(hi_20) else None,
    })


def _supply_shock_reversal(row: pd.Series, hist: pd.DataFrame) -> PatternMatch:
    """최근 3일 급락+순매도 후 오늘 반전 캔들+거래량."""
    if len(hist) < 4:
        return PatternMatch(False, 0.0, {})
    recent = hist.iloc[-4:-1]  # 오늘 제외한 직전 3봉
    net3 = float(recent["foreign_net_val"].sum() + recent["inst_net_val"].sum())
    tv3 = float(recent["traded_value"].sum())
    supply_pct = net3 / tv3 if tv3 > 0 else 0.0
    sold = supply_pct < -0.03
    rng = row["high"] - row["low"]
    lower_shadow = (min(row["open"], row["close"]) - row["low"]) / rng if rng > 0 else 0
    close_pos = float(row.get("close_pos") or 0)
    vol_ratio = float(row.get("vol_ratio") or 0)
    matched = bool(sold and close_pos >= 0.7 and lower_shadow >= 0.25 and vol_ratio >= 1.3)
    strength = float(np.clip(
        (abs(supply_pct) / 0.10) * 0.4
        + close_pos * 0.3
        + min(lower_shadow / 0.4, 1) * 0.3,
        0, 1))
    return PatternMatch(matched, strength, {
        "prior_3d_supply": round(supply_pct, 4),
        "lower_shadow": round(float(lower_shadow), 3),
        "close_pos": round(close_pos, 3),
    })


def _broker_stealth_accumulation(row: pd.Series, hist: pd.DataFrame) -> PatternMatch:
    """상위 5거래원 편중 강함, 그러나 일일 변동성 낮음 (조용한 매집)."""
    broker_5d = float(row.get("broker_imbalance_5d") or 0)
    if len(hist) < 5:
        return PatternMatch(False, 0.0, {})
    vol_5d = float(hist["return_pct"].iloc[-5:].std() or 0)
    matched = bool(broker_5d >= 0.10 and vol_5d < 0.015)
    strength = float(np.clip(
        (broker_5d / 0.20) * 0.6
        + (1 - min(vol_5d / 0.02, 1)) * 0.4,
        0, 1))
    return PatternMatch(matched, strength, {
        "broker_5d": round(broker_5d, 4),
        "realized_vol_5d": round(vol_5d, 4),
    })


def _pullback_to_ema20(row: pd.Series, hist: pd.DataFrame) -> PatternMatch:
    """직전 5일 상승 후 EMA20 지지 확인 + 수급 유지."""
    if len(hist) < 6 or pd.isna(row.get("ema20")):
        return PatternMatch(False, 0.0, {})
    ret_5d = float(row["close"] / hist["close"].iloc[-6] - 1)
    dist = float(row["close"] / row["ema20"] - 1)
    supply = float((row.get("foreign_ratio_5d") or 0) + (row.get("inst_ratio_5d") or 0))
    matched = bool(ret_5d >= 0.05 and -0.01 <= dist <= 0.02 and supply >= 0)
    strength = float(np.clip(
        min(ret_5d / 0.15, 1) * 0.5
        + (1 - abs(dist) / 0.02) * 0.5,
        0, 1))
    return PatternMatch(matched, strength, {
        "prior_5d_ret": round(ret_5d, 4),
        "dist_to_ema20": round(dist, 4),
    })


PATTERNS: list[Pattern] = [
    Pattern("accumulation_breakout",
            "5일 수급 매집 + 20일 신고가 브레이크아웃 + 거래량",
            _accumulation_breakout, forward_window=5, tp=0.05, sl=-0.03),
    Pattern("supply_shock_reversal",
            "3일 급락 순매도 후 반전 캔들 + 거래량",
            _supply_shock_reversal, forward_window=3, tp=0.04, sl=-0.025),
    Pattern("broker_stealth_accumulation",
            "상위 거래원 편중 + 낮은 변동성 (조용한 매집)",
            _broker_stealth_accumulation, forward_window=10, tp=0.08, sl=-0.04),
    Pattern("pullback_to_ema20",
            "직전 5일 상승 후 EMA20 지지 + 수급 유지",
            _pullback_to_ema20, forward_window=3, tp=0.04, sl=-0.02),
]

PATTERNS_BY_NAME = {p.name: p for p in PATTERNS}
