"""Event-driven 백테스트: 종가 진입 → 익일 이후 SL/TP/time 청산."""
from __future__ import annotations

import pandas as pd

from .signals import SignalConfig, close_entry_signal, exit_signal


def run_backtest(
    df: pd.DataFrame,
    cfg: SignalConfig,
    max_hold: int = 3,
    stop_loss: float = -0.03,
    take_profit: float = 0.05,
    warmup: int = 60,
) -> tuple[pd.DataFrame, dict]:
    trades = []
    n = len(df)
    i = warmup
    while i < n - 1:
        row = df.iloc[i]
        sig = close_entry_signal(row, cfg)
        if not sig["enter"]:
            i += 1
            continue

        entry_price = float(row["close"])
        entry_date = row["date"]
        entry_score = sig["score"]
        held = 0
        exit_price = None
        exit_reason = None
        exit_date = None
        j = i + 1
        while j < n and held < max_hold:
            held += 1
            fwd = df.iloc[j]
            ex = exit_signal(fwd, entry_price, held, stop_loss, take_profit, max_hold)
            if ex["exit"]:
                exit_price = ex["price"]
                exit_reason = ex["reason"]
                exit_date = fwd["date"]
                break
            j += 1
        if exit_price is None:
            fwd = df.iloc[min(j, n - 1)]
            exit_price = float(fwd["close"])
            exit_reason = "eod"
            exit_date = fwd["date"]

        ret = exit_price / entry_price - 1
        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry": round(entry_price, 0),
            "exit": round(exit_price, 0),
            "ret": round(ret, 4),
            "reason": exit_reason,
            "score": round(entry_score, 1),
        })
        # 청산 이후로 이동 (신호 중복 방지)
        i = j + 1 if exit_date is not None else i + 1

    trades_df = pd.DataFrame(trades)
    stats = summarize(trades_df) if len(trades_df) else {"trades": 0}
    return trades_df, stats


def summarize(t: pd.DataFrame) -> dict:
    wins = t[t["ret"] > 0]
    losses = t[t["ret"] <= 0]
    win_rate = len(wins) / len(t) if len(t) else 0.0
    avg_win = wins["ret"].mean() if len(wins) else 0.0
    avg_loss = losses["ret"].mean() if len(losses) else 0.0
    payoff = abs(avg_win / avg_loss) if avg_loss < 0 else float("inf")
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    equity = (1 + t["ret"]).cumprod()
    peak = equity.cummax()
    mdd = ((equity - peak) / peak).min() if len(equity) else 0.0
    reason_mix = t["reason"].value_counts().to_dict()
    return {
        "trades": int(len(t)),
        "win_rate": round(win_rate, 3),
        "avg_win": round(float(avg_win), 4),
        "avg_loss": round(float(avg_loss), 4),
        "payoff_ratio": round(payoff, 2) if payoff != float("inf") else None,
        "expectancy_per_trade": round(float(expectancy), 4),
        "total_return": round(float((1 + t["ret"]).prod() - 1), 4),
        "max_drawdown": round(float(mdd), 4),
        "exit_reasons": reason_mix,
    }
