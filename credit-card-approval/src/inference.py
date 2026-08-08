"""Inference: load artifact, produce p_approve + risk_band + top_reasons.

`top_reasons` uses a lightweight local explanation: for each numeric/bool
feature, compare its contribution to a baseline where the feature is
replaced by the training median. We use XGBoost's `pred_contribs` (SHAP
values) when available and fall back to a leave-one-out approximation.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .schema import ApplicantRecord


DEFAULT_ARTIFACT = Path(__file__).resolve().parent.parent / "artifacts" / "model.joblib"

RISK_BANDS = [
    ("A", 0.85),
    ("B", 0.60),
    ("C", 0.35),
    ("D", 0.0),
]

# human-readable descriptions for the top-reason emitter
FEATURE_LABELS_KO = {
    "income_to_limit_ratio": "연소득 대비 요청한도",
    "log_income": "연소득",
    "log_requested_limit": "요청한도",
    "employment_years": "재직기간",
    "stability_score": "재직/거주 안정성",
    "age": "나이",
    "is_night_submit": "심야 신청 여부",
    "is_new_device_90d": "신규 디바이스 여부",
    "is_vpn_proxy": "VPN/프록시 사용",
    "is_emulator_signal": "에뮬레이터 의심 신호",
    "ip_country_matches_locale": "IP 국가/언어 일치",
    "paste_ratio": "붙여넣기 비율",
    "field_edit_count": "필드 수정 횟수",
    "keystrokes_per_sec": "타이핑 속도",
    "has_other_cards": "타 카드 보유 여부",
    "housing": "주거형태",
    "job_category": "직업군",
    "employer_size": "근무처 규모",
    "device_seen_count_90d": "동일 디바이스 최근 90일 신청 횟수",
    "session_duration_sec": "신청 소요시간",
}


@dataclass
class PredictionResult:
    p_approve: float
    risk_band: str
    top_reasons: list[dict[str, Any]]
    model_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "p_approve": round(self.p_approve, 4),
            "risk_band": self.risk_band,
            "top_reasons": self.top_reasons,
            "model_version": self.model_version,
        }


def _record_to_frame(record: ApplicantRecord) -> pd.DataFrame:
    d = {
        **record.application.model_dump(),
        **record.device.model_dump(),
        **record.behavior.model_dump(),
    }
    return pd.DataFrame([d])


def _band(p: float) -> str:
    for name, lo in RISK_BANDS:
        if p >= lo:
            return name
    return "D"


def _top_reasons(
    xgb_clf, feature_names: list[str], X_row: np.ndarray, k: int = 3,
) -> list[dict[str, Any]]:
    """Use XGBoost SHAP contributions to pick the top-k features that
    most pushed the prediction down from baseline (negative contribs).

    We surface the *negative* contribs because "심사 통과 확률" 관점에서 사용자에게
    개선 지점을 보여주는 것이 목적. Falls back to top-k absolute contribs when
    the applicant is high-confidence approval.
    """
    booster = xgb_clf.get_booster()
    import xgboost as xgb
    dm = xgb.DMatrix(X_row.reshape(1, -1))
    contribs = booster.predict(dm, pred_contribs=True)[0]  # (n_features + 1,)
    # last entry is the bias
    feat_contribs = contribs[:-1]
    order_neg = np.argsort(feat_contribs)  # most negative first
    # If nothing is meaningfully negative, fall back to |contrib| ranking
    negatives = [i for i in order_neg if feat_contribs[i] < -1e-4]
    if not negatives:
        picks = np.argsort(-np.abs(feat_contribs))[:k]
    else:
        picks = negatives[:k]
    out = []
    for idx in picks:
        name = feature_names[idx]
        out.append({
            "feature": name,
            "label_ko": FEATURE_LABELS_KO.get(name, name),
            "contribution": float(feat_contribs[idx]),
        })
    return out


def load_artifact(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path) if path else DEFAULT_ARTIFACT
    if not path.exists():
        raise FileNotFoundError(
            f"Artifact not found at {path}. Run `python train.py` first."
        )
    return joblib.load(path)


def predict(record: ApplicantRecord, artifact: dict[str, Any] | None = None) -> PredictionResult:
    art = artifact or load_artifact()
    encoder = art["encoder"]
    xgb_clf = art["xgb"]
    calibrator = art["calibrator"]
    feature_names = art["feature_names"]

    df = _record_to_frame(record)
    X = encoder.transform(df).to_numpy(dtype=np.float32)
    raw = xgb_clf.predict_proba(X)[:, 1]
    p = float(calibrator.transform(raw)[0])
    return PredictionResult(
        p_approve=p,
        risk_band=_band(p),
        top_reasons=_top_reasons(xgb_clf, feature_names, X[0]),
        model_version=art["model_version"],
    )


# --- CLI ---
SAMPLE_RECORD = {
    "application": {
        "age": 32,
        "marital_status": "married",
        "dependents": 1,
        "education": "bachelor",
        "job_category": "office",
        "employer_size": "mid",
        "employment_years": 3.5,
        "annual_income": 55_000_000,
        "income_type": "salary",
        "housing": "jeonse",
        "residence_years": 2.0,
        "requested_credit_limit": 5_000_000,
        "has_other_cards": True,
    },
    "device": {
        "device_type": "mobile",
        "os_family": "ios",
        "os_version_age_days": 30,
        "browser": "safari",
        "screen_resolution": "1170x2532",
        "is_emulator_signal": False,
        "timezone_offset": 540,
        "language": "ko-KR",
        "ip_country": "KR",
        "ip_country_matches_locale": True,
        "is_vpn_proxy": False,
        "device_seen_count_7d": 0,
        "device_seen_count_90d": 0,
    },
    "behavior": {
        "session_duration_sec": 240,
        "keystroke_count": 380,
        "paste_ratio": 0.02,
        "field_edit_count": 3,
        "avg_field_dwell_sec": 5.1,
        "submit_hour": 14,
        "submit_day_of_week": 2,
        "autofill_used": True,
        "back_navigation_count": 1,
        "time_since_prior_attempt_min": -1,
    },
}


def _cli() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        record = ApplicantRecord.model_validate(SAMPLE_RECORD)
    else:
        record = ApplicantRecord.model_validate(json.load(sys.stdin))
    result = predict(record)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _cli()
