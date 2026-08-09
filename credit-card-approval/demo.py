"""Multi-scenario demo. Loads the trained artifact and runs several
representative applications to illustrate what the model does."""
from __future__ import annotations

import copy
import json
from typing import Any

from src.inference import SAMPLE_RECORD, load_artifact, predict
from src.schema import ApplicantRecord


def _override(base: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """Deep-copy base and set dotted-path overrides."""
    d = copy.deepcopy(base)
    for path, val in overrides.items():
        section, key = path.split(".")
        d[section][key] = val
    return d


SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "1) 정석 신청자 — 대기업 3.5년차, 자가아님, 요청한도 500만",
        SAMPLE_RECORD,
    ),
    (
        "2) 신입 사회초년생 — 24세, 6개월차, 소득 3천만",
        _override(
            SAMPLE_RECORD,
            **{
                "application.age": 24,
                "application.employment_years": 0.5,
                "application.annual_income": 30_000_000,
                "application.employer_size": "small",
                "application.requested_credit_limit": 2_000_000,
                "application.education": "bachelor",
            },
        ),
    ),
    (
        "3) 자영업자 — 42세, 소득 8천만, 요청한도 3천만 (한도 과다)",
        _override(
            SAMPLE_RECORD,
            **{
                "application.age": 42,
                "application.job_category": "self_employed",
                "application.employer_size": "none",
                "application.income_type": "business",
                "application.annual_income": 80_000_000,
                "application.employment_years": 8.0,
                "application.requested_credit_limit": 30_000_000,
            },
        ),
    ),
    (
        "4) 심야 대량 붙여넣기 — 브로커 대필 의심",
        _override(
            SAMPLE_RECORD,
            **{
                "behavior.submit_hour": 3,
                "behavior.paste_ratio": 0.75,
                "behavior.field_edit_count": 0,
                "behavior.session_duration_sec": 45,
                "behavior.autofill_used": False,
            },
        ),
    ),
    (
        "5) VPN + 해외 IP + 에뮬레이터 — 사기신청 의심",
        _override(
            SAMPLE_RECORD,
            **{
                "device.is_vpn_proxy": True,
                "device.ip_country": "CN",
                "device.ip_country_matches_locale": False,
                "device.is_emulator_signal": True,
            },
        ),
    ),
    (
        "6) 무직 + 고한도 요청",
        _override(
            SAMPLE_RECORD,
            **{
                "application.job_category": "unemployed",
                "application.employer_size": "none",
                "application.annual_income": 3_000_000,
                "application.employment_years": 0.0,
                "application.requested_credit_limit": 20_000_000,
            },
        ),
    ),
]


BAR_WIDTH = 40


def _bar(p: float) -> str:
    filled = int(round(p * BAR_WIDTH))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def main() -> None:
    art = load_artifact()
    version = art["model_version"]
    print(f"Model {version}\n")
    print("=" * 92)

    for title, rec in SCENARIOS:
        result = predict(ApplicantRecord.model_validate(rec), artifact=art)
        p = result.p_approve
        print(f"\n{title}")
        print(f"  p_approve : {p:.3f}   |{_bar(p)}|   → band {result.risk_band}")
        print(f"  주요 감점 요인 (SHAP contribution):")
        for r in result.top_reasons:
            contrib = r["contribution"]
            arrow = "↓" if contrib < 0 else "↑"
            print(f"     {arrow} {r['label_ko']:<22s}  ({contrib:+.3f})")

    print("\n" + "=" * 92)
    print("등급 정책:  A ≥ 0.85  |  B 0.60-0.85  |  C 0.35-0.60  |  D < 0.35")


if __name__ == "__main__":
    main()
