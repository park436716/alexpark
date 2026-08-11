"""CLI: 최신봉 신호 조회 / 백테스트 실행."""
from __future__ import annotations

import argparse

from .backtest import run_backtest
from .features import build_features
from .mock_data import generate_mock_ohlcv_flows
from .signals import SignalConfig, close_entry_signal


def _load(args):
    # 지금은 mock 만. 실제 데이터는 여기서 KIS API 어댑터를 붙이면 됨.
    return generate_mock_ohlcv_flows(days=args.days, seed=args.seed)


def cmd_signal(args):
    df = build_features(_load(args))
    row = df.iloc[-1]
    cfg = SignalConfig(entry_score_threshold=args.threshold)
    sig = close_entry_signal(row, cfg)

    print(f"date        : {row['date'].date()}")
    print(f"close       : {row['close']:.0f}")
    print(f"ema20       : {row['ema20']:.0f}   dist: {(row['close']/row['ema20']-1)*100:+.2f}%")
    print(f"vol_ratio   : {row['vol_ratio']:.2f}x")
    print(f"close_pos   : {row['close_pos']:.2f}   (0=저가, 1=고가)")
    if row['resistance'] == row['resistance']:  # not NaN
        print(f"resistance  : {row['resistance']:.0f}   gap: {row['dist_to_resistance']*100:+.2f}%")

    print("\n-- 수급 5일 누적 (거래대금 대비) --")
    print(f"  foreign  : {row['foreign_ratio_5d']*100:+.2f}%")
    print(f"  inst     : {row['inst_ratio_5d']*100:+.2f}%")
    print(f"  prog     : {row['prog_nonarb_ratio_5d']*100:+.2f}%")
    print(f"  broker   : {row['broker_imbalance_5d']*100:+.2f}%")

    print(f"\n>>> SIGNAL: {'BUY' if sig['enter'] else 'HOLD'}   score={sig['score']:.1f}")
    comp = {k: round(v, 2) for k, v in sig["components"].items() if k != "score"}
    print(f"    components: {comp}")
    if sig["reasons"]:
        print(f"    rejections: {', '.join(sig['reasons'])}")


def cmd_backtest(args):
    df = build_features(_load(args))
    cfg = SignalConfig(entry_score_threshold=args.threshold)
    trades, stats = run_backtest(
        df, cfg,
        max_hold=args.hold,
        stop_loss=args.sl,
        take_profit=args.tp,
    )

    print("=== Backtest summary ===")
    for k, v in stats.items():
        print(f"  {k:22s} {v}")
    if len(trades):
        print("\n=== Last 15 trades ===")
        print(trades.tail(15).to_string(index=False))


def main():
    p = argparse.ArgumentParser(description="종가매매 수급분석 프로토타입")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = dict(days=(int, 500), seed=(int, 42), threshold=(float, 55.0))

    s = sub.add_parser("signal", help="최신봉에 대한 신호 평가")
    for k, (t, dv) in common.items():
        s.add_argument(f"--{k}", type=t, default=dv)
    s.set_defaults(func=cmd_signal)

    b = sub.add_parser("backtest", help="합성 데이터로 백테스트")
    for k, (t, dv) in common.items():
        b.add_argument(f"--{k}", type=t, default=dv)
    b.add_argument("--hold", type=int, default=3, help="최대 보유 영업일")
    b.add_argument("--sl", type=float, default=-0.03, help="손절 (예: -0.03 = -3%)")
    b.add_argument("--tp", type=float, default=0.05, help="익절 (예: 0.05 = +5%)")
    b.set_defaults(func=cmd_backtest)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
