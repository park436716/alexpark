"""Training: XGBoost + isotonic calibration + LR baseline.

Saves a single joblib artifact containing everything inference needs:
    - encoder (FeatureEncoder)
    - xgb model
    - isotonic calibrator
    - feature names
    - training metadata
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import evaluate
from .features import FeatureEncoder


MODEL_VERSION = "v0.1.0"


@dataclass
class TrainMetadata:
    model_version: str
    n_train: int
    n_valid: int
    n_test: int
    xgb_params: dict[str, Any] = field(default_factory=dict)
    valid_report: dict[str, float] = field(default_factory=dict)
    test_report: dict[str, float] = field(default_factory=dict)
    baseline_valid_auc: float = 0.0


def train_xgb(
    X_train: np.ndarray, y_train: np.ndarray,
    X_valid: np.ndarray, y_valid: np.ndarray,
) -> xgb.XGBClassifier:
    params = dict(
        n_estimators=600,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=5,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="auc",
        tree_method="hist",
        early_stopping_rounds=40,
        random_state=42,
    )
    clf = xgb.XGBClassifier(**params)
    clf.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        verbose=False,
    )
    return clf


def train_lr_baseline(
    X_train: np.ndarray, y_train: np.ndarray,
) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000, C=1.0)),
    ]).fit(X_train, y_train)


def fit_calibrator(
    raw_valid: np.ndarray, y_valid: np.ndarray,
) -> IsotonicRegression:
    cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    cal.fit(raw_valid, y_valid)
    return cal


def train_and_save(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    artifact_path: str | Path,
) -> TrainMetadata:
    encoder = FeatureEncoder().fit(train_df)
    X_train = encoder.transform(train_df).to_numpy(dtype=np.float32)
    X_valid = encoder.transform(valid_df).to_numpy(dtype=np.float32)
    X_test = encoder.transform(test_df).to_numpy(dtype=np.float32)
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    y_valid = valid_df["label"].to_numpy(dtype=np.int64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    xgb_clf = train_xgb(X_train, y_train, X_valid, y_valid)
    lr_clf = train_lr_baseline(X_train, y_train)

    raw_valid = xgb_clf.predict_proba(X_valid)[:, 1]
    raw_test = xgb_clf.predict_proba(X_test)[:, 1]
    calibrator = fit_calibrator(raw_valid, y_valid)

    p_valid = calibrator.transform(raw_valid)
    p_test = calibrator.transform(raw_test)
    lr_valid_prob = lr_clf.predict_proba(X_valid)[:, 1]

    valid_report = evaluate.evaluate(y_valid, p_valid)
    test_report = evaluate.evaluate(y_test, p_test)
    baseline_auc = float(evaluate.roc_auc_score(y_valid, lr_valid_prob))

    meta = TrainMetadata(
        model_version=MODEL_VERSION,
        n_train=int(len(train_df)),
        n_valid=int(len(valid_df)),
        n_test=int(len(test_df)),
        xgb_params={k: v for k, v in xgb_clf.get_params().items()
                    if isinstance(v, (int, float, str, bool, type(None)))},
        valid_report=asdict(valid_report),
        test_report=asdict(test_report),
        baseline_valid_auc=baseline_auc,
    )

    artifact = {
        "model_version": MODEL_VERSION,
        "encoder": encoder,
        "xgb": xgb_clf,
        "calibrator": calibrator,
        "feature_names": encoder.feature_names(),
        "metadata": asdict(meta),
    }
    artifact_path = Path(artifact_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path)

    # human-readable sidecar
    sidecar = artifact_path.with_suffix(".meta.json")
    sidecar.write_text(json.dumps(asdict(meta), indent=2, default=str))

    return meta
