"""CLI: 최신봉 신호 조회 / 백테스트 / Digital Analyst 실행."""
from __future__ import annotations

import argparse

from .analyst import MonitoringPlan, Ticker, print_notes, run_analyst
from .backtest import run_backtest
from .features import build_features
from .mock_data import generate_mock_ohlcv_flows
from .patterns import PATTERNS, PATTERNS_BY_NAME, compute_forward_odds
from .signals import SignalConfig, close_entry_signal


def _load(args):
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
    if row['resistance'] == row['resistance']:
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
        df, cfg, max_hold=args.hold, stop_loss=args.sl, take_profit=args.tp,
    )
    print("=== Backtest summary ===")
    for k, v in stats.items():
        print(f"  {k:22s} {v}")
    if len(trades):
        print("\n=== Last 15 trades ===")
        print(trades.tail(15).to_string(index=False))


def cmd_patterns(args):
    """Pattern 라이브러리 캘리브레이션: 각 셋업의 forward odds."""
    df = build_features(_load(args))
    print(f"=== Pattern library calibration (n_bars={len(df)}) ===\n")
    print(f"{'pattern':36s} {'n':>4} {'WR':>8} {'avg_win':>9} "
          f"{'avg_loss':>9} {'E':>9} {'payoff':>7}")
    print("-" * 90)
    for p in PATTERNS:
        if args.only and p.name not in args.only.split(","):
            continue
        o = compute_forward_odds(df, p)
        print(f"{p.name:36s} {o.n:>4d} {o.hit_rate*100:>7.1f}% "
              f"{o.avg_win*100:>+8.2f}% {o.avg_loss*100:>+8.2f}% "
              f"{o.expectancy*100:>+8.2f}% {o.payoff:>7.2f}")
    print("\n(설명)")
    for p in PATTERNS:
        if args.only and p.name not in args.only.split(","):
            continue
        print(f"  {p.name}: {p.description}  [window={p.forward_window}d, "
              f"TP={p.tp*100:+.1f}%, SL={p.sl*100:+.1f}%]")


def cmd_analyst(args):
    """Digital Analyst — 감시 종목 × Pattern 조합의 일일 분석노트."""
    tickers = [
        Ticker(symbol="AAA", name="Alpha Corp"),
        Ticker(symbol="BBB", name="Beta Inc"),
        Ticker(symbol="CCC", name="Gamma Ltd"),
    ]
    dfs = {}
    for i, t in enumerate(tickers):
        raw = generate_mock_ohlcv_flows(days=args.days, seed=args.seed + i)
        dfs[t.symbol] = build_features(raw)

    plan = MonitoringPlan(
        tickers=tickers,
        patterns=args.patterns.split(",") if args.patterns else [],
        lookback_days_for_odds=args.lookback,
    )
    notes = run_analyst(dfs, plan)

    # Latest-bar 매치를 상위에 두고 조용한 PASS 는 숨김
    print_notes(notes, show_pass=args.show_pass)


def main():
    p = argparse.ArgumentParser(description="종가매매 수급분석 + Digital Analyst 프로토타입")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = dict(days=(int, 500), seed=(int, 42), threshold=(float, 55.0))

    s = sub.add_parser("signal", help="최신봉 신호 평가 (원시 signal.py)")
    for k, (t, dv) in common.items():
        s.add_argument(f"--{k}", type=t, default=dv)
    s.set_defaults(func=cmd_signal)

    b = sub.add_parser("backtest", help="signal.py 로직 백테스트")
    for k, (t, dv) in common.items():
        b.add_argument(f"--{k}", type=t, default=dv)
    b.add_argument("--hold", type=int, default=3)
    b.add_argument("--sl", type=float, default=-0.03)
    b.add_argument("--tp", type=float, default=0.05)
    b.set_defaults(func=cmd_backtest)

    pt = sub.add_parser("patterns", help="Pattern 라이브러리 forward odds 캘리브레이션")
    pt.add_argument("--days", type=int, default=1000)
    pt.add_argument("--seed", type=int, default=42)
    pt.add_argument("--only", type=str, default="",
                    help="쉼표로 구분된 pattern 이름만 표시")
    pt.set_defaults(func=cmd_patterns)

    an = sub.add_parser("analyst", help="Digital Analyst — 감시 종목 × Pattern 일일 노트")
    an.add_argument("--days", type=int, default=500)
    an.add_argument("--seed", type=int, default=42)
    an.add_argument("--lookback", type=int, default=500,
                    help="odds 계산용 lookback 영업일")
    an.add_argument("--patterns", type=str, default="",
                    help="쉼표로 구분된 pattern 이름만 사용 (기본: 전체)")
    an.add_argument("--show-pass", action="store_true",
                    help="조건 미성립 PASS 도 표시")
    an.set_defaults(func=cmd_analyst)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
