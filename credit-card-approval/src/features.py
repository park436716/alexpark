"""Feature engineering.

Adds derived features then packs into a matrix suitable for XGBoost.
Categorical columns are label-encoded via a stable dict per column.
Missing values (in the columns that allow them) are preserved as NaN
so XGBoost's built-in missing-value handling routes them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


CATEGORICAL_COLS = [
    "marital_status", "education", "job_category", "employer_size",
    "income_type", "housing", "device_type", "os_family", "browser",
    "ip_country",
]

BOOL_COLS = [
    "has_other_cards", "is_emulator_signal", "ip_country_matches_locale",
    "is_vpn_proxy", "autofill_used",
]

NUMERIC_COLS = [
    "age", "dependents", "employment_years", "annual_income",
    "residence_years", "requested_credit_limit",
    "os_version_age_days", "timezone_offset",
    "device_seen_count_7d", "device_seen_count_90d",
    "session_duration_sec", "keystroke_count", "paste_ratio",
    "field_edit_count", "avg_field_dwell_sec", "submit_hour",
    "submit_day_of_week", "back_navigation_count",
    "time_since_prior_attempt_min",
]

DERIVED_COLS = [
    "income_to_limit_ratio",
    "log_income",
    "log_requested_limit",
    "stability_score",
    "is_night_submit",
    "is_new_device_90d",
    "keystrokes_per_sec",
    "age_bucket",
]


@dataclass
class FeatureEncoder:
    """Fit-once, apply-many. Learns categorical label maps on the training
    set, applies them consistently to valid/test/inference."""
    category_maps: dict[str, dict[str, int]] = field(default_factory=dict)

    def fit(self, df: pd.DataFrame) -> "FeatureEncoder":
        for col in CATEGORICAL_COLS:
            uniq = df[col].astype("string").fillna("__missing__").unique().tolist()
            uniq.sort()
            self.category_maps[col] = {v: i for i, v in enumerate(uniq)}
        # age_bucket also categorical, but derived — learn its map too
        buckets = ["20s_and_below", "30s", "40s", "50s", "60s_plus"]
        self.category_maps["age_bucket"] = {v: i for i, v in enumerate(buckets)}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)

        # numeric passthrough
        for col in NUMERIC_COLS:
            out[col] = pd.to_numeric(df[col], errors="coerce")

        # bool → int (keep NaN as NaN)
        for col in BOOL_COLS:
            s = df[col]
            out[col] = s.astype("float64")  # True→1.0, False→0.0, NA→NaN

        # categorical → int via learned map (unseen → NaN)
        for col in CATEGORICAL_COLS:
            m = self.category_maps.get(col, {})
            s = df[col].astype("string").fillna("__missing__")
            out[col] = s.map(m).astype("float64")

        # derived
        income = pd.to_numeric(df["annual_income"], errors="coerce")
        limit = pd.to_numeric(df["requested_credit_limit"], errors="coerce")
        out["income_to_limit_ratio"] = income / limit.clip(lower=1)
        out["log_income"] = np.log1p(income.clip(lower=0))
        out["log_requested_limit"] = np.log1p(limit.clip(lower=0))
        emp = pd.to_numeric(df["employment_years"], errors="coerce").fillna(0)
        res = pd.to_numeric(df["residence_years"], errors="coerce").fillna(0)
        out["stability_score"] = emp + 0.5 * res
        hour = pd.to_numeric(df["submit_hour"], errors="coerce")
        out["is_night_submit"] = ((hour >= 0) & (hour < 5)).astype("float64")
        seen90 = pd.to_numeric(df["device_seen_count_90d"], errors="coerce")
        out["is_new_device_90d"] = (seen90.fillna(0) == 0).astype("float64")
        dur = pd.to_numeric(df["session_duration_sec"], errors="coerce")
        keys = pd.to_numeric(df["keystroke_count"], errors="coerce")
        out["keystrokes_per_sec"] = keys / dur.clip(lower=1)

        age = pd.to_numeric(df["age"], errors="coerce").fillna(0)
        bucket_str = pd.cut(
            age, bins=[-1, 29, 39, 49, 59, 200],
            labels=["20s_and_below", "30s", "40s", "50s", "60s_plus"],
        ).astype("string")
        m = self.category_maps["age_bucket"]
        out["age_bucket"] = bucket_str.map(m).astype("float64")

        return out[NUMERIC_COLS + BOOL_COLS + CATEGORICAL_COLS + DERIVED_COLS]

    def feature_names(self) -> list[str]:
        return NUMERIC_COLS + BOOL_COLS + CATEGORICAL_COLS + DERIVED_COLS


def build_matrix(df: pd.DataFrame, encoder: FeatureEncoder) -> np.ndarray:
    return encoder.transform(df).to_numpy(dtype=np.float32)
