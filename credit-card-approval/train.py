"""End-to-end training script.

Usage:
    python train.py                     # 20k samples, default seed
    python train.py --n 50000           # bigger dataset
    python train.py --artifact ./m.pkl  # custom path
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.data import GenConfig, generate, time_based_split
from src.model import train_and_save
from src.report_export import build_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20_000, help="synthetic sample count")
    parser.add_argument("--seed", type=int, default=20260808)
    parser.add_argument(
        "--artifact", type=Path,
        default=Path(__file__).parent / "artifacts" / "model.joblib",
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="If set, also write a JSON dashboard report to this path.",
    )
    args = parser.parse_args()

    print(f"[1/4] Generating {args.n} synthetic applications ...")
    df = generate(GenConfig(n_samples=args.n, seed=args.seed))
    print(f"      approval rate = {df['label'].mean():.3f}")

    print("[2/4] Time-based split (train / valid / test) ...")
    train_df, valid_df, test_df = time_based_split(df)
    print(f"      sizes: {len(train_df)} / {len(valid_df)} / {len(test_df)}")

    print("[3/4] Training XGBoost + LR baseline + isotonic calibration ...")
    meta = train_and_save(train_df, valid_df, test_df, args.artifact)

    print(f"[4/4] Saved artifact to {args.artifact}")
    print()
    print("=== Validation ===")
    for k, v in meta.valid_report.items():
        print(f"  {k:20s} = {v:.4f}" if isinstance(v, (int, float)) else f"  {k:20s} = {v}")
    print(f"  LR baseline AUC       = {meta.baseline_valid_auc:.4f}")
    print()
    print("=== Test ===")
    for k, v in meta.test_report.items():
        print(f"  {k:20s} = {v:.4f}" if isinstance(v, (int, float)) else f"  {k:20s} = {v}")

    if args.report is not None:
        print()
        print(f"[+] Writing dashboard report to {args.report} ...")
        import joblib
        artifact = joblib.load(args.artifact)
        build_report(train_df, valid_df, test_df, artifact, args.report)
        print("    done.")


if __name__ == "__main__":
    main()
