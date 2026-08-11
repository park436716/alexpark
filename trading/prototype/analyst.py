"""Digital Analyst — Patterns × Monitoring Plan → 매일 분석노트.

Modest Proposal 프레임의 "Process":
    Monitoring Plan(감시 종목/셋업 리스트) 을 매일 저녁 돌려서
    각 (종목 × 셋업) 조합에 대해:
      - 조건 성립 여부
      - 성립 강도 (strength)
      - 이 셋업의 forward odds (실측)
      - 조합한 edge_score = strength × expectancy
      - BUY / WATCH / PASS + 향후 감시할 것
    을 뽑아낸다. LLM 은 이 노트 위에 얹어서 뉴스·공시·차트를 종합.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .patterns import (
    PATTERNS,
    PATTERNS_BY_NAME,
    ForwardOdds,
    Pattern,
    compute_forward_odds,
)


@dataclass
class Ticker:
    symbol: str
    name: str = ""


@dataclass
class MonitoringPlan:
    tickers: list[Ticker]
    patterns: list[str] = field(default_factory=list)  # empty = all patterns
    lookback_days_for_odds: int = 500


@dataclass
class AnalystNote:
    date: pd.Timestamp
    symbol: str
    pattern: str
    matched: bool
    strength: float
    forward_odds: ForwardOdds
    edge_score: float
    detail: dict
    recommendation: str
    monitoring: str


def _select_patterns(plan: MonitoringPlan) -> list[Pattern]:
    if not plan.patterns:
        return PATTERNS
    return [PATTERNS_BY_NAME[n] for n in plan.patterns if n in PATTERNS_BY_NAME]


def _classify(pattern: Pattern, matched: bool, strength: float,
              odds: ForwardOdds) -> tuple[str, str]:
    if matched and odds.expectancy > 0 and strength >= 0.6:
        return ("BUY",
                f"진입 후 {pattern.forward_window}영업일 내 "
                f"TP {pattern.tp*100:+.1f}% / SL {pattern.sl*100:+.1f}% 첫 터치 청산. "
                f"익일 시가 갭 확인 후 재평가.")
    if matched and odds.expectancy > 0:
        return ("WATCH",
                f"조건 성립. strength={strength:.2f} 낮음 — "
                f"다음 봉에서 거래량/수급 재확인.")
    if matched:
        return ("PASS",
                f"조건 성립하나 forward odds 나쁨 "
                f"(E={odds.expectancy*100:+.2f}%). skip.")
    return ("PASS", "조건 미성립. 감시 유지.")


def run_analyst(df_by_ticker: dict[str, pd.DataFrame],
                plan: MonitoringPlan) -> list[AnalystNote]:
    patterns = _select_patterns(plan)
    notes: list[AnalystNote] = []
    for ticker in plan.tickers:
        df = df_by_ticker.get(ticker.symbol)
        if df is None or len(df) < 60:
            continue
        latest = df.iloc[-1]
        hist = df.iloc[max(0, len(df) - 61):]
        odds_slice = df.iloc[max(0, len(df) - plan.lookback_days_for_odds):]
        for pattern in patterns:
            match = pattern.detect(latest, hist)
            odds = compute_forward_odds(odds_slice, pattern)
            edge = odds.expectancy * match.strength
            rec, mon = _classify(pattern, match.matched, match.strength, odds)
            notes.append(AnalystNote(
                date=latest["date"],
                symbol=ticker.symbol,
                pattern=pattern.name,
                matched=match.matched,
                strength=round(match.strength, 3),
                forward_odds=odds,
                edge_score=round(edge, 4),
                detail=match.detail,
                recommendation=rec,
                monitoring=mon,
            ))
    return notes


def print_notes(notes: list[AnalystNote], show_pass: bool = False) -> None:
    priority = {"BUY": 0, "WATCH": 1, "PASS": 2}
    ordered = sorted(notes, key=lambda n: (priority[n.recommendation], -n.edge_score))
    shown = 0
    print(f"\n=== Digital Analyst — {len(ordered)} notes ===\n")
    for n in ordered:
        if n.recommendation == "PASS" and not n.matched and not show_pass:
            continue
        o = n.forward_odds
        print(f"[{n.recommendation}] {n.symbol}  {n.pattern}")
        print(f"   date={n.date.date()}  matched={n.matched}  strength={n.strength}")
        print(f"   odds: n={o.n}  WR={o.hit_rate*100:.1f}%  "
              f"avg_win={o.avg_win*100:+.2f}%  avg_loss={o.avg_loss*100:+.2f}%  "
              f"E={o.expectancy*100:+.2f}%  payoff={o.payoff}")
        print(f"   edge_score={n.edge_score}  detail={n.detail}")
        print(f"   → {n.monitoring}\n")
        shown += 1
    if shown == 0:
        print("(none matched — 조용한 날)")
