"""Smoke tests: generate a tiny dataset, train, then run one inference."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.data import GenConfig, generate, time_based_split
from src.inference import SAMPLE_RECORD, load_artifact, predict
from src.model import train_and_save
from src.schema import ApplicantRecord


def test_end_to_end():
    df = generate(GenConfig(n_samples=3000, seed=7))
    train_df, valid_df, test_df = time_based_split(df, valid_days=60, test_days=30)
    assert len(train_df) > 0 and len(valid_df) > 0 and len(test_df) > 0

    with tempfile.TemporaryDirectory() as tmp:
        artifact_path = Path(tmp) / "model.joblib"
        meta = train_and_save(train_df, valid_df, test_df, artifact_path)
        assert meta.valid_report["auc"] > 0.6  # sanity, not a benchmark

        art = load_artifact(artifact_path)
        record = ApplicantRecord.model_validate(SAMPLE_RECORD)
        result = predict(record, artifact=art)
        assert 0.0 <= result.p_approve <= 1.0
        assert result.risk_band in {"A", "B", "C", "D"}
        assert len(result.top_reasons) >= 1
