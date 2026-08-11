"""종가매매 진입/청산 신호.

전략 개요:
    - 판단 시점: 장 마감 30분 전 (14:50 KST)
    - 진입 시점: 종가 근처 매수
    - 청산: 익일 시가 or SL/TP 도달
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SignalConfig:
    # 하드 필터 (모두 통과해야 후보)
    min_vol_ratio: float = 1.5           # 거래량 20일 평균 대비 배수
    min_close_pos: float = 0.65          # 종가가 당일 range 상위 35% 내
    min_ema20_dist: float = -0.02        # 종가가 EMA20 -2% 이내 이상
    max_ema20_dist: float = 0.08         # EMA20 +8% 이내 (과열 방지)
    # 저항 gap: 음수면 브레이크아웃 허용. -0.02 = 저항 2% 위까지 허용.
    # 이 필터를 원치 않으면 -inf 로 설정.
    min_resistance_gap: float = -0.02

    # 스코어 컷오프
    entry_score_threshold: float = 55.0  # 0~100

    # 수급 스코어 가중치 (합계 100)
    w_foreign: float = 25.0
    w_inst: float = 25.0
    w_prog: float = 15.0
    w_broker: float = 15.0
    w_price_action: float = 10.0
    w_volume: float = 10.0

    # 정규화 스케일 (5일 누적 순매수비율이 이 값이면 만점)
    scale_foreign_5d: float = 0.10
    scale_inst_5d: float = 0.10
    scale_prog_5d: float = 0.08
    scale_broker_5d: float = 0.15
    scale_vol_ratio: float = 2.5         # vol_ratio 2.5 → 만점


def _clip01(x: float) -> float:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    return float(np.clip(x, 0.0, 1.0))


def score_components(row: pd.Series, cfg: SignalConfig) -> dict:
    f = _clip01(row.get("foreign_ratio_5d", 0.0) / cfg.scale_foreign_5d)
    i = _clip01(row.get("inst_ratio_5d", 0.0) / cfg.scale_inst_5d)
    p = _clip01(row.get("prog_nonarb_ratio_5d", 0.0) / cfg.scale_prog_5d)
    b = _clip01(row.get("broker_imbalance_5d", 0.0) / cfg.scale_broker_5d)
    pa = _clip01(row.get("close_pos", 0.0))
    # 브레이크아웃 보너스: dist_to_resistance <= 0 → 종가가 최근 저항을 이미 뚫음
    dr = row.get("dist_to_resistance")
    if pd.notna(dr) and dr <= 0.0:
        pa = _clip01(pa + 0.3)
    v = _clip01((row.get("vol_ratio", 0.0) - 1.0) / (cfg.scale_vol_ratio - 1.0))
    total = (
        cfg.w_foreign * f
        + cfg.w_inst * i
        + cfg.w_prog * p
        + cfg.w_broker * b
        + cfg.w_price_action * pa
        + cfg.w_volume * v
    )
    return {"score": float(total), "foreign": f, "inst": i, "prog": p,
            "broker": b, "price_action": pa, "volume": v}


def close_entry_signal(row: pd.Series, cfg: SignalConfig) -> dict:
    """종가매매 진입 신호. 하드 필터 → 스코어 컷오프."""
    reasons = []
    ok = True

    ema20 = row.get("ema20")
    close = row.get("close")
    if pd.isna(ema20) or pd.isna(close):
        return {"enter": False, "score": 0.0, "components": {}, "reasons": ["warmup"]}

    if close < ema20 * (1 + cfg.min_ema20_dist):
        ok = False; reasons.append("below_ema20")
    if close > ema20 * (1 + cfg.max_ema20_dist):
        ok = False; reasons.append("extended_from_ema20")
    if row.get("vol_ratio", 0) < cfg.min_vol_ratio:
        ok = False; reasons.append("low_volume")
    if row.get("close_pos", 0) < cfg.min_close_pos:
        ok = False; reasons.append("weak_close")

    dr = row.get("dist_to_resistance")
    if pd.notna(dr) and dr < cfg.min_resistance_gap:
        ok = False; reasons.append("at_resistance")

    comp = score_components(row, cfg)
    if comp["score"] < cfg.entry_score_threshold:
        ok = False; reasons.append(f"score<{cfg.entry_score_threshold:.0f}")

    return {"enter": ok, "score": comp["score"], "components": comp, "reasons": reasons}


def exit_signal(row: pd.Series, entry_price: float, held_days: int,
                stop_loss: float, take_profit: float, max_hold: int) -> dict:
    """익일 이후 청산 판정 (다음 봉 high/low 대비 SL/TP)."""
    if row["low"] / entry_price - 1 <= stop_loss:
        return {"exit": True, "price": entry_price * (1 + stop_loss), "reason": "sl"}
    if row["high"] / entry_price - 1 >= take_profit:
        return {"exit": True, "price": entry_price * (1 + take_profit), "reason": "tp"}
    if held_days >= max_hold:
        return {"exit": True, "price": row["close"], "reason": "time"}
    return {"exit": False}
