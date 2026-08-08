"""Synthetic dataset generator.

The label-generating process (LGP) below is deliberately simple and
interpretable — it lets us verify the training pipeline works end-to-end
without needing real approval data. Real deployment must be trained on
observed approvals.

LGP intent:
- Older, stably employed, higher-income applicants have higher approval
  odds (business intuition, not causal claim).
- Suspicious device/behavior signals (VPN, emulator, high paste ratio,
  new device, night submits, bot-like edit counts) sharply reduce odds.
- income_to_limit_ratio strongly matters — asking for a limit too large
  for your income is a common decline reason.
- Noise added so no model reaches AUC=1.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


RNG_SEED = 20260808


@dataclass
class GenConfig:
    n_samples: int = 20_000
    seed: int = RNG_SEED
    # base rate for approval before feature effects, ~65% approval overall
    base_logit: float = 0.9
    # noise added to logit
    noise_scale: float = 0.9


_JOB_CATS = ["office", "professional", "civil_servant", "self_employed",
             "freelancer", "student", "part_time", "unemployed", "other"]
_JOB_P    = [0.28, 0.10, 0.08, 0.15, 0.08, 0.06, 0.08, 0.05, 0.12]

_EDU      = ["middle_school", "high_school", "college", "bachelor", "graduate"]
_EDU_P    = [0.03, 0.28, 0.14, 0.44, 0.11]

_HOUSING  = ["owned", "jeonse", "monthly_rent", "family_owned"]
_HOUSING_P = [0.35, 0.30, 0.25, 0.10]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate(config: GenConfig | None = None) -> pd.DataFrame:
    """Return a DataFrame with one row per applicant + `label` and `event_ts`.

    `event_ts` is uniformly spread over the last 365 days so callers can
    do a time-based split.
    """
    cfg = config or GenConfig()
    rng = np.random.default_rng(cfg.seed)
    n = cfg.n_samples

    # --- application ---
    age = rng.integers(19, 70, size=n)
    marital_status = rng.choice(
        ["single", "married", "divorced", "widowed"], size=n,
        p=[0.40, 0.50, 0.08, 0.02],
    )
    dependents = np.where(
        marital_status == "married",
        rng.integers(0, 4, size=n),
        rng.integers(0, 2, size=n),
    )
    education = rng.choice(_EDU, size=n, p=_EDU_P)
    job_category = rng.choice(_JOB_CATS, size=n, p=_JOB_P)
    employer_size = rng.choice(
        ["large", "mid", "small", "gov", "none"], size=n,
        p=[0.22, 0.28, 0.32, 0.08, 0.10],
    )
    # employment_years correlates with age but with wide spread
    employment_years = np.clip(
        rng.normal(loc=(age - 22) * 0.4, scale=3.0), 0, 40,
    )
    # income depends on age, education, employer size
    edu_boost = np.select(
        [education == "graduate", education == "bachelor",
         education == "college", education == "high_school"],
        [1.35, 1.15, 1.00, 0.85],
        default=0.75,
    )
    emp_boost = np.select(
        [employer_size == "large", employer_size == "gov",
         employer_size == "mid", employer_size == "small"],
        [1.30, 1.10, 1.00, 0.85],
        default=0.60,
    )
    base_income = 30_000_000 + (age - 20) * 800_000
    annual_income = np.clip(
        base_income * edu_boost * emp_boost
        * rng.lognormal(mean=0.0, sigma=0.25, size=n),
        0, 500_000_000,
    ).astype(int)
    # unemployed / student overrides
    annual_income = np.where(
        (job_category == "unemployed") | (job_category == "student"),
        rng.integers(0, 15_000_000, size=n),
        annual_income,
    )
    income_type = np.where(
        np.isin(job_category, ["self_employed", "freelancer"]),
        "business",
        "salary",
    )
    housing = rng.choice(_HOUSING, size=n, p=_HOUSING_P)
    residence_years = np.clip(rng.exponential(scale=3.0, size=n), 0, 30)
    # requested limit: median ~ 30% of annual income, heavy right tail
    requested_credit_limit = np.clip(
        annual_income * rng.beta(a=2.0, b=5.0, size=n),
        500_000, 100_000_000,
    ).astype(int)
    has_other_cards = rng.random(n) < 0.55

    # --- device ---
    device_type = rng.choice(
        ["mobile", "tablet", "desktop"], size=n, p=[0.72, 0.05, 0.23],
    )
    os_family = np.where(
        device_type == "mobile",
        rng.choice(["ios", "android"], size=n, p=[0.55, 0.45]),
        rng.choice(["windows", "mac", "linux"], size=n, p=[0.70, 0.27, 0.03]),
    )
    os_version_age_days = np.clip(rng.exponential(scale=90, size=n), 0, 1500).astype(int)
    browser = rng.choice(
        ["chrome", "safari", "edge", "firefox", "samsung", "other"], size=n,
        p=[0.45, 0.30, 0.10, 0.05, 0.08, 0.02],
    )
    is_emulator_signal = rng.random(n) < 0.02
    timezone_offset = np.where(rng.random(n) < 0.97, 540, rng.choice([-480, 0, 60, 480], size=n))
    ip_country = np.where(rng.random(n) < 0.96, "KR", rng.choice(["US", "CN", "VN", "JP"], size=n))
    ip_country_matches_locale = ip_country == "KR"
    is_vpn_proxy = rng.random(n) < 0.03
    # most devices are new to us
    device_seen_count_7d = np.where(rng.random(n) < 0.90, 0, rng.integers(1, 6, size=n))
    device_seen_count_90d = np.where(rng.random(n) < 0.80, 0, rng.integers(1, 12, size=n))

    # --- behavior ---
    session_duration_sec = np.clip(rng.normal(loc=210, scale=90, size=n), 15, 3600).astype(int)
    keystroke_count = np.clip(session_duration_sec * rng.uniform(1.2, 3.0, size=n), 20, 5000).astype(int)
    paste_ratio = np.clip(rng.beta(a=1.5, b=15.0, size=n), 0, 1)
    field_edit_count = rng.poisson(lam=2.5, size=n)
    avg_field_dwell_sec = np.clip(rng.normal(loc=4.5, scale=1.5, size=n), 0.2, 30)
    submit_hour = rng.integers(0, 24, size=n)
    submit_day_of_week = rng.integers(0, 7, size=n)
    autofill_used = rng.random(n) < 0.45
    back_navigation_count = rng.poisson(lam=1.0, size=n)
    time_since_prior_attempt_min = np.where(
        rng.random(n) < 0.85, -1, rng.integers(0, 60 * 24 * 30, size=n),
    )

    # Simulate ~2% adversarial applications: fake, high paste, fresh device, VPN
    adversarial = rng.random(n) < 0.02
    paste_ratio = np.where(adversarial, np.clip(paste_ratio + 0.6, 0, 1), paste_ratio)
    is_vpn_proxy = is_vpn_proxy | (adversarial & (rng.random(n) < 0.6))
    field_edit_count = np.where(adversarial, 0, field_edit_count)
    submit_hour = np.where(adversarial, rng.integers(1, 5, size=n), submit_hour)

    # --- label-generating process ---
    income_to_limit = annual_income / np.clip(requested_credit_limit, 1, None)
    logit = np.full(n, cfg.base_logit, dtype=float)
    logit += 0.020 * (age - 30)
    logit += 0.10 * employment_years
    logit += 0.55 * np.log1p(annual_income / 1e7)
    logit += 0.35 * np.log1p(income_to_limit)
    logit += 0.15 * has_other_cards.astype(float)
    logit += 0.20 * (housing == "owned").astype(float)
    logit -= 0.60 * (job_category == "unemployed").astype(float)
    logit -= 0.30 * (job_category == "part_time").astype(float)
    logit -= 0.25 * (employer_size == "none").astype(float)
    logit += 0.10 * residence_years / 10.0

    # device/behavior penalties
    logit -= 1.20 * is_vpn_proxy.astype(float)
    logit -= 1.00 * is_emulator_signal.astype(float)
    logit -= 0.80 * (~ip_country_matches_locale).astype(float)
    logit -= 2.5 * np.maximum(paste_ratio - 0.3, 0)   # only high paste hurts
    logit -= 0.02 * np.abs(submit_hour - 14)          # midday is best
    logit -= 0.30 * (field_edit_count == 0).astype(float)
    logit += 0.10 * autofill_used.astype(float)
    logit -= 0.60 * adversarial.astype(float)

    logit += rng.normal(loc=0.0, scale=cfg.noise_scale, size=n)
    p = _sigmoid(logit)
    label = (rng.random(n) < p).astype(int)

    # --- event_ts spread over past 365 days ---
    now = datetime(2026, 8, 8)
    offsets_days = rng.uniform(0, 365, size=n)
    event_ts = [now - timedelta(days=float(d)) for d in offsets_days]

    return pd.DataFrame({
        "event_ts": event_ts,
        "age": age,
        "marital_status": marital_status,
        "dependents": dependents,
        "education": education,
        "job_category": job_category,
        "employer_size": employer_size,
        "employment_years": employment_years,
        "annual_income": annual_income,
        "income_type": income_type,
        "housing": housing,
        "residence_years": residence_years,
        "requested_credit_limit": requested_credit_limit,
        "has_other_cards": has_other_cards,
        "device_type": device_type,
        "os_family": os_family,
        "os_version_age_days": os_version_age_days,
        "browser": browser,
        "is_emulator_signal": is_emulator_signal,
        "timezone_offset": timezone_offset,
        "ip_country": ip_country,
        "ip_country_matches_locale": ip_country_matches_locale,
        "is_vpn_proxy": is_vpn_proxy,
        "device_seen_count_7d": device_seen_count_7d,
        "device_seen_count_90d": device_seen_count_90d,
        "session_duration_sec": session_duration_sec,
        "keystroke_count": keystroke_count,
        "paste_ratio": paste_ratio,
        "field_edit_count": field_edit_count,
        "avg_field_dwell_sec": avg_field_dwell_sec,
        "submit_hour": submit_hour,
        "submit_day_of_week": submit_day_of_week,
        "autofill_used": autofill_used,
        "back_navigation_count": back_navigation_count,
        "time_since_prior_attempt_min": time_since_prior_attempt_min,
        "label": label,
    })


def time_based_split(
    df: pd.DataFrame,
    valid_days: int = 60,
    test_days: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological split. Assumes df has `event_ts`."""
    df = df.sort_values("event_ts").reset_index(drop=True)
    latest = df["event_ts"].max()
    test_cut = latest - timedelta(days=test_days)
    valid_cut = test_cut - timedelta(days=valid_days)
    train = df[df["event_ts"] < valid_cut].reset_index(drop=True)
    valid = df[(df["event_ts"] >= valid_cut) & (df["event_ts"] < test_cut)].reset_index(drop=True)
    test = df[df["event_ts"] >= test_cut].reset_index(drop=True)
    return train, valid, test
