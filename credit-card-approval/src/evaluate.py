"""Evaluation metrics: AUC, KS, Brier, ECE, PSI."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score


@dataclass
class EvalReport:
    auc: float
    pr_auc: float
    ks: float
    brier: float
    ece: float
    approval_rate: float
    pred_approval_rate: float

    def pretty(self) -> str:
        return (
            f"  ROC-AUC   = {self.auc:.4f}\n"
            f"  PR-AUC    = {self.pr_auc:.4f}\n"
            f"  KS        = {self.ks:.4f}\n"
            f"  Brier     = {self.brier:.4f}\n"
            f"  ECE       = {self.ece:.4f}\n"
            f"  actual y=1 rate = {self.approval_rate:.4f}\n"
            f"  mean p_approve  = {self.pred_approval_rate:.4f}"
        )


def ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Two-sample KS between score distributions of positives and negatives."""
    pos = np.sort(y_score[y_true == 1])
    neg = np.sort(y_score[y_true == 0])
    if len(pos) == 0 or len(neg) == 0:
        return 0.0
    grid = np.sort(np.concatenate([pos, neg]))
    cdf_pos = np.searchsorted(pos, grid, side="right") / len(pos)
    cdf_neg = np.searchsorted(neg, grid, side="right") / len(neg)
    return float(np.max(np.abs(cdf_pos - cdf_neg)))


def expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10,
) -> float:
    """ECE with equal-width bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi if i < n_bins - 1 else y_prob <= hi)
        if not np.any(mask):
            continue
        avg_p = float(np.mean(y_prob[mask]))
        avg_y = float(np.mean(y_true[mask]))
        ece += (np.sum(mask) / n) * abs(avg_p - avg_y)
    return float(ece)


def evaluate(y_true: np.ndarray, y_prob: np.ndarray) -> EvalReport:
    return EvalReport(
        auc=float(roc_auc_score(y_true, y_prob)),
        pr_auc=float(average_precision_score(y_true, y_prob)),
        ks=ks_statistic(y_true, y_prob),
        brier=float(brier_score_loss(y_true, y_prob)),
        ece=expected_calibration_error(y_true, y_prob),
        approval_rate=float(np.mean(y_true)),
        pred_approval_rate=float(np.mean(y_prob)),
    )


def psi(reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
    """Population Stability Index between two score distributions."""
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    cuts = np.quantile(reference, quantiles)
    cuts[0] = -np.inf
    cuts[-1] = np.inf
    ref_hist, _ = np.histogram(reference, bins=cuts)
    cur_hist, _ = np.histogram(current, bins=cuts)
    ref_p = np.clip(ref_hist / max(len(reference), 1), 1e-6, None)
    cur_p = np.clip(cur_hist / max(len(current), 1), 1e-6, None)
    return float(np.sum((cur_p - ref_p) * np.log(cur_p / ref_p)))
