"""Feature engineering: OHLCV + supply/demand → model-ready columns.

입력 컬럼(필수):
    date, open, high, low, close, volume,
    foreign_net_val, inst_net_val, retail_net_val,
    prog_arb_net_val, prog_nonarb_net_val,
    top5_buyer_net_val, top5_seller_net_val
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_moving_averages(df: pd.DataFrame, windows=(5, 20, 60)) -> pd.DataFrame:
    for w in windows:
        df[f"ema{w}"] = df["close"].ewm(span=w, adjust=False).mean()
        df[f"sma{w}"] = df["close"].rolling(w).mean()
    return df


def add_volume_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    df["vol_sma20"] = df["volume"].rolling(window).mean()
    df["vol_ratio"] = df["volume"] / df["vol_sma20"]
    df["traded_value"] = df["close"] * df["volume"]
    df["tv_sma20"] = df["traded_value"].rolling(window).mean()
    return df


def add_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    body = (df["close"] - df["open"]).abs()
    df["body_ratio"] = body / rng
    df["close_pos"] = (df["close"] - df["low"]) / rng
    top = df[["close", "open"]].max(axis=1)
    df["upper_shadow"] = (df["high"] - top) / rng
    df["gap_pct"] = df["open"] / df["close"].shift(1) - 1
    df["return_pct"] = df["close"] / df["close"].shift(1) - 1
    return df


def add_pivot_sr(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """Nearest pivot-based S/R from a rolling window of past highs/lows."""
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    n = len(df)
    resistance = np.full(n, np.nan)
    support = np.full(n, np.nan)
    for i in range(lookback, n):
        wh = highs[i - lookback : i]
        wl = lows[i - lookback : i]
        c = closes[i]
        above = wh[wh > c]
        below = wl[wl < c]
        if above.size:
            resistance[i] = above.min()
        if below.size:
            support[i] = below.max()
    df["resistance"] = resistance
    df["support"] = support
    df["dist_to_resistance"] = df["resistance"] / df["close"] - 1
    df["dist_to_support"] = df["close"] / df["support"] - 1
    return df


def add_supply_demand(df: pd.DataFrame, roll: int = 5) -> pd.DataFrame:
    """수급 지표 정규화: 순매수 대금 / 거래대금 → 규모 무관 비율."""
    tv = df["traded_value"].replace(0, np.nan)
    df["foreign_ratio"] = df["foreign_net_val"] / tv
    df["inst_ratio"] = df["inst_net_val"] / tv
    df["prog_nonarb_ratio"] = df["prog_nonarb_net_val"] / tv
    df["broker_imbalance"] = (
        df["top5_buyer_net_val"] - df["top5_seller_net_val"]
    ) / tv
    for col in ("foreign_ratio", "inst_ratio", "prog_nonarb_ratio", "broker_imbalance"):
        df[f"{col}_{roll}d"] = df[col].rolling(roll).sum()
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True).copy()
    df = add_moving_averages(df)
    df = add_volume_features(df)
    df = add_candle_features(df)
    df = add_pivot_sr(df)
    df = add_supply_demand(df)
    return df
