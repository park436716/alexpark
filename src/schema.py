"""Feature schema (Pydantic v2).

Mirrors docs/design.md §2. Used to validate a single applicant record at
inference time. Fields with `= None` are optional (JS may be disabled,
IP intel API may fail, etc.); the pipeline emits `_is_missing` flags.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt


JobCategory = Literal[
    "office", "professional", "civil_servant", "self_employed",
    "freelancer", "student", "part_time", "unemployed", "other",
]
IncomeType = Literal["salary", "business", "pension", "other"]
Housing = Literal["owned", "jeonse", "monthly_rent", "family_owned"]
EmployerSize = Literal["large", "mid", "small", "gov", "none"]
Education = Literal["middle_school", "high_school", "college", "bachelor", "graduate"]
DeviceType = Literal["mobile", "tablet", "desktop"]
OsFamily = Literal["ios", "android", "windows", "mac", "linux", "other"]


class Application(BaseModel):
    age: int = Field(ge=18, le=100)
    marital_status: Literal["single", "married", "divorced", "widowed"]
    dependents: NonNegativeInt
    education: Education
    job_category: JobCategory
    employer_size: EmployerSize
    employment_years: NonNegativeFloat
    annual_income: NonNegativeFloat            # KRW
    income_type: IncomeType
    housing: Housing
    residence_years: NonNegativeFloat
    requested_credit_limit: NonNegativeFloat   # KRW
    has_other_cards: bool


class Device(BaseModel):
    device_type: DeviceType
    os_family: OsFamily
    os_version_age_days: Optional[NonNegativeInt] = None
    browser: Optional[str] = None
    screen_resolution: Optional[str] = None
    is_emulator_signal: Optional[bool] = None
    timezone_offset: Optional[int] = None      # minutes; KR = 540
    language: Optional[str] = None             # e.g. "ko-KR"
    ip_country: Optional[str] = None           # ISO-2
    ip_country_matches_locale: Optional[bool] = None
    is_vpn_proxy: Optional[bool] = None
    device_seen_count_7d: Optional[NonNegativeInt] = None
    device_seen_count_90d: Optional[NonNegativeInt] = None


class Behavior(BaseModel):
    session_duration_sec: Optional[NonNegativeInt] = None
    keystroke_count: Optional[NonNegativeInt] = None
    paste_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    field_edit_count: Optional[NonNegativeInt] = None
    avg_field_dwell_sec: Optional[NonNegativeFloat] = None
    submit_hour: Optional[int] = Field(default=None, ge=0, le=23)
    submit_day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    autofill_used: Optional[bool] = None
    back_navigation_count: Optional[NonNegativeInt] = None
    time_since_prior_attempt_min: Optional[int] = None  # -1 = first attempt


class ApplicantRecord(BaseModel):
    """One inference input."""
    application: Application
    device: Device
    behavior: Behavior


ALL_FEATURE_NAMES = [
    # application
    "age", "marital_status", "dependents", "education", "job_category",
    "employer_size", "employment_years", "annual_income", "income_type",
    "housing", "residence_years", "requested_credit_limit", "has_other_cards",
    # device
    "device_type", "os_family", "os_version_age_days", "browser",
    "screen_resolution", "is_emulator_signal", "timezone_offset", "language",
    "ip_country", "ip_country_matches_locale", "is_vpn_proxy",
    "device_seen_count_7d", "device_seen_count_90d",
    # behavior
    "session_duration_sec", "keystroke_count", "paste_ratio",
    "field_edit_count", "avg_field_dwell_sec", "submit_hour",
    "submit_day_of_week", "autofill_used", "back_navigation_count",
    "time_since_prior_attempt_min",
]
