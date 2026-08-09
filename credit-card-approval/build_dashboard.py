"""Assemble the interactive HTML dashboard by injecting report_data.json
into the template. Run after `python train.py --report artifacts/report_data.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent


def main() -> Path:
    data = json.loads((HERE / "artifacts/report_data.json").read_text())
    template = (HERE / "dashboard.template.html").read_text()
    marker = "__REPORT_DATA__"
    if marker not in template:
        raise SystemExit(f"Template missing {marker} marker")
    injected = template.replace(marker, json.dumps(data, ensure_ascii=False))
    out = HERE / "dashboard.html"
    out.write_text(injected)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    return out


if __name__ == "__main__":
    main()
