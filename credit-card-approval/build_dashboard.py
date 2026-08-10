"""Assemble the interactive HTML pages by injecting report_data.json
into each template. Run after
    python train.py --report artifacts/report_data.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
MARKER = "__REPORT_DATA__"


def _build(template_name: str, out_name: str, data_json: str) -> Path:
    template = (HERE / template_name).read_text()
    if MARKER not in template:
        raise SystemExit(f"{template_name} missing {MARKER} marker")
    injected = template.replace(MARKER, data_json)
    out = HERE / out_name
    out.write_text(injected)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    return out


def main() -> None:
    data = json.loads((HERE / "artifacts/report_data.json").read_text())
    data_json = json.dumps(data, ensure_ascii=False)
    _build("dashboard.template.html", "dashboard.html", data_json)
    _build("customer.template.html", "customer.html", data_json)


if __name__ == "__main__":
    main()
