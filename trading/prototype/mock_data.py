"""합성 OHLCV + 수급 데이터 생성기.

실 KIS API 데이터를 붙이기 전 시그널/백테스트 로직 검증용.
가끔씩 '기관/외인이 조용히 매집하는 축적 구간' 을 심어 두어,
수급 스코어가 진입 신호로 이어지는지 확인할 수 있게 했다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_mock_ohlcv_flows(days: int = 250, seed: int = 42,
                              start: str = "2025-01-02",
                              start_price: float = 50_000.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    price = start_price
    rows = []
    accum_left = 0

    for d in range(days):
        # 5% 확률로 축적 구간 시작 (3~7영업일 지속)
        if accum_left <= 0 and rng.random() < 0.05:
            accum_left = int(rng.integers(3, 8))

        if accum_left > 0:
            drift = 0.010
            foreign_bias = rng.normal(0.030, 0.015)
            inst_bias = rng.normal(0.030, 0.015)
            prog_bias = rng.normal(0.020, 0.012)
            broker_bias = rng.normal(0.050, 0.020)
            vol_mult = float(rng.uniform(1.4, 2.5))
            accum_left -= 1
        else:
            drift = float(rng.normal(0.001, 0.003))
            foreign_bias = rng.normal(-0.005, 0.020)
            inst_bias = rng.normal(-0.005, 0.020)
            prog_bias = rng.normal(0.000, 0.015)
            broker_bias = rng.normal(0.000, 0.030)
            vol_mult = float(rng.uniform(0.7, 1.3))

        vol_pct = max(0.005, float(rng.normal(0.02, 0.008)))
        open_p = price * (1 + float(rng.normal(0, 0.005)))
        close_p = open_p * (1 + drift + float(rng.normal(0, vol_pct)))
        high = max(open_p, close_p) * (1 + abs(float(rng.normal(0, 0.010))))
        low = min(open_p, close_p) * (1 - abs(float(rng.normal(0, 0.010))))
        volume = int(500_000 * vol_mult * (1 + abs(float(rng.normal(0, 0.2)))))
        tv = close_p * volume

        rows.append({
            "date": pd.Timestamp(start) + pd.tseries.offsets.BDay(d),
            "open": round(open_p, 0),
            "high": round(high, 0),
            "low": round(low, 0),
            "close": round(close_p, 0),
            "volume": volume,
            "foreign_net_val": int(tv * foreign_bias),
            "inst_net_val": int(tv * inst_bias),
            "retail_net_val": -int(tv * (foreign_bias + inst_bias)),
            "prog_arb_net_val": int(tv * float(rng.normal(0, 0.01))),
            "prog_nonarb_net_val": int(tv * prog_bias),
            "top5_buyer_net_val": int(tv * max(0.0, broker_bias + float(rng.normal(0, 0.02)))),
            "top5_seller_net_val": int(tv * max(0.0, -broker_bias + float(rng.normal(0, 0.02)))),
        })
        price = close_p

    return pd.DataFrame(rows)
