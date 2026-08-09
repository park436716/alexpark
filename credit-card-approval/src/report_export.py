"""Assemble a self-contained report_data.json for the HTML dashboard.

Includes:
- Metrics (valid + test)
- Curve data (ROC, PR, calibration reliability)
- Score distributions for approvals vs rejections
- XGBoost feature importance
- Preset scenario predictions with SHAP reasons
- Threshold sweep policy table
- LR baseline export (coefficients + preprocessing state) so the browser
  can score arbitrary applicants in real time as sliders move.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

from . import features as ft
from .evaluate import evaluate as evaluate_metrics
from .features import FeatureEncoder
from .inference import FEATURE_LABELS_KO, SAMPLE_RECORD, _top_reasons, predict
from .schema import ApplicantRecord


def _thin(xs: np.ndarray, ys: np.ndarray, n: int = 200) -> list[dict[str, float]]:
    """Sub-sample a curve to n points, keeping endpoints."""
    if len(xs) <= n:
        idx = np.arange(len(xs))
    else:
        idx = np.linspace(0, len(xs) - 1, n).astype(int)
    return [{"x": float(xs[i]), "y": float(ys[i])} for i in idx]


def _calibration_curve(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10):
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi if i < n_bins - 1 else y_prob <= hi)
        if not np.any(mask):
            continue
        out.append({
            "mean_p": float(np.mean(y_prob[mask])),
            "observed": float(np.mean(y_true[mask])),
            "n": int(np.sum(mask)),
            "lo": float(lo),
            "hi": float(hi),
        })
    return out


def _score_histogram(scores: np.ndarray, n_bins: int = 40):
    counts, edges = np.histogram(scores, bins=n_bins, range=(0.0, 1.0))
    return [
        {"lo": float(edges[i]), "hi": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]


def _threshold_sweep(y_prob: np.ndarray) -> list[dict[str, float]]:
    """Simulate a two-cutoff policy. `p >= T_high` → auto-approve (skip CB);
    `p < T_low` → auto-decline; the middle band goes to CB review.

    Returns rows for the reader to see how each pair of cutoffs performs.
    """
    rows = []
    for t_high, t_low in [
        (0.90, 0.30), (0.85, 0.35), (0.80, 0.40), (0.75, 0.45), (0.70, 0.50),
    ]:
        auto_approve = float(np.mean(y_prob >= t_high))
        auto_decline = float(np.mean(y_prob < t_low))
        cb_review = 1.0 - auto_approve - auto_decline
        rows.append({
            "t_high": t_high,
            "t_low": t_low,
            "auto_approve_pct": auto_approve,
            "cb_review_pct": cb_review,
            "auto_decline_pct": auto_decline,
        })
    return rows


def _feature_importance(xgb_clf, feature_names: list[str], top_n: int = 15):
    booster = xgb_clf.get_booster()
    score = booster.get_score(importance_type="gain")
    pairs = []
    for i, name in enumerate(feature_names):
        key = f"f{i}"
        pairs.append({"name": name, "importance": float(score.get(key, 0.0))})
    pairs.sort(key=lambda r: -r["importance"])
    return pairs[:top_n]


def _preset_scenarios(art: dict[str, Any]) -> list[dict[str, Any]]:
    from .inference import predict as _predict

    scenarios = [
        {"title": "정석 신청자", "subtitle": "대기업 3.5년차, 요청한도 500만", "override": {}},
        {"title": "사회초년생", "subtitle": "24세, 재직 6개월, 소득 3천만", "override": {
            "application.age": 24, "application.employment_years": 0.5,
            "application.annual_income": 30_000_000,
            "application.employer_size": "small",
            "application.requested_credit_limit": 2_000_000,
        }},
        {"title": "자영업자·한도 과다", "subtitle": "42세, 소득 8천, 요청한도 3천만", "override": {
            "application.age": 42, "application.job_category": "self_employed",
            "application.employer_size": "none", "application.income_type": "business",
            "application.annual_income": 80_000_000, "application.employment_years": 8.0,
            "application.requested_credit_limit": 30_000_000,
        }},
        {"title": "심야 대량 붙여넣기", "subtitle": "브로커 대필 의심", "override": {
            "behavior.submit_hour": 3, "behavior.paste_ratio": 0.75,
            "behavior.field_edit_count": 0, "behavior.session_duration_sec": 45,
            "behavior.autofill_used": False,
        }},
        {"title": "VPN·해외 IP·에뮬레이터", "subtitle": "사기신청 의심", "override": {
            "device.is_vpn_proxy": True, "device.ip_country": "CN",
            "device.ip_country_matches_locale": False, "device.is_emulator_signal": True,
        }},
        {"title": "무직 + 고한도", "subtitle": "재직 0년, 요청한도 2천만", "override": {
            "application.job_category": "unemployed", "application.employer_size": "none",
            "application.annual_income": 3_000_000, "application.employment_years": 0.0,
            "application.requested_credit_limit": 20_000_000,
        }},
    ]

    out = []
    for s in scenarios:
        rec = json.loads(json.dumps(SAMPLE_RECORD))
        for path, val in s["override"].items():
            section, key = path.split(".")
            rec[section][key] = val
        result = _predict(ApplicantRecord.model_validate(rec), artifact=art)
        out.append({
            "title": s["title"],
            "subtitle": s["subtitle"],
            "p_approve": result.p_approve,
            "risk_band": result.risk_band,
            "top_reasons": result.top_reasons,
        })
    return out


def _lr_export(train_df: pd.DataFrame, y_train: np.ndarray) -> dict[str, Any]:
    """Train a JS-portable LR model on the encoded matrix and export
    everything needed to score in the browser: means, stds, coefficients,
    intercept, category maps, feature names."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    encoder = FeatureEncoder().fit(train_df)
    X = encoder.transform(train_df).to_numpy(dtype=np.float32)
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000, C=1.0)),
    ]).fit(X, y_train)

    imputer = pipe.named_steps["impute"]
    scaler = pipe.named_steps["scale"]
    lr = pipe.named_steps["lr"]

    return {
        "feature_names": encoder.feature_names(),
        "numeric_cols": ft.NUMERIC_COLS,
        "bool_cols": ft.BOOL_COLS,
        "categorical_cols": ft.CATEGORICAL_COLS,
        "derived_cols": ft.DERIVED_COLS,
        "category_maps": encoder.category_maps,
        "medians": imputer.statistics_.tolist(),
        "means": scaler.mean_.tolist(),
        "stds": scaler.scale_.tolist(),
        "coef": lr.coef_[0].tolist(),
        "intercept": float(lr.intercept_[0]),
    }


def build_report(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    artifact: dict[str, Any],
    out_path: Path,
) -> Path:
    xgb_clf = artifact["xgb"]
    calibrator = artifact["calibrator"]
    encoder = artifact["encoder"]
    feature_names = artifact["feature_names"]

    def _prob(df: pd.DataFrame) -> np.ndarray:
        X = encoder.transform(df).to_numpy(dtype=np.float32)
        raw = xgb_clf.predict_proba(X)[:, 1]
        return calibrator.transform(raw)

    p_valid = _prob(valid_df)
    p_test = _prob(test_df)
    y_valid = valid_df["label"].to_numpy(dtype=np.int64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    fpr, tpr, _ = roc_curve(y_test, p_test)
    prec, rec, _ = precision_recall_curve(y_test, p_test)

    report = {
        "model_version": artifact["model_version"],
        "training": {
            "n_train": int(len(train_df)),
            "n_valid": int(len(valid_df)),
            "n_test": int(len(test_df)),
            "train_approval_rate": float(train_df["label"].mean()),
            "test_approval_rate": float(y_test.mean()),
        },
        "metrics_valid": evaluate_metrics(y_valid, p_valid).__dict__,
        "metrics_test": evaluate_metrics(y_test, p_test).__dict__,
        "roc": _thin(fpr, tpr, 200),
        "pr":  _thin(rec, prec, 200),
        "calibration": _calibration_curve(y_test, p_test),
        "score_hist_pos": _score_histogram(p_test[y_test == 1]),
        "score_hist_neg": _score_histogram(p_test[y_test == 0]),
        "feature_importance": _feature_importance(xgb_clf, feature_names, 15),
        "preset_scenarios": _preset_scenarios(artifact),
        "threshold_sweep": _threshold_sweep(p_test),
        "lr_export": _lr_export(train_df, train_df["label"].to_numpy(dtype=np.int64)),
        "feature_labels_ko": FEATURE_LABELS_KO,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False))
    return out_path
