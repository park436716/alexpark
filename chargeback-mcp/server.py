"""Chargeback Rules MCP server.

Exposes reason-code lookup, evidence checklists, and cross-network comparison
tools over the Model Context Protocol (stdio transport).

Assumes rule PDFs are served from an internal document server; this demo
loads pre-summarized rules from data/rules.json.

Run:
    python3 server.py

Or wire into an MCP client via stdio.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).parent
RULES = json.loads((ROOT / "data" / "rules.json").read_text())
CONTEXTS = json.loads((ROOT / "data" / "contexts.json").read_text())

mcp = FastMCP("chargeback-rules")


def _network(net_key: str) -> dict[str, Any]:
    key = net_key.lower()
    if key not in RULES["networks"]:
        raise ValueError(f"Unknown network: {net_key}. Use one of: visa, mastercard, amex.")
    return RULES["networks"][key]


@mcp.tool()
def list_networks() -> list[dict[str, str]]:
    """List supported card networks and their dispute frameworks."""
    return [
        {"key": k, "name": v["name"], "framework": v["framework"], "source": v["source"]}
        for k, v in RULES["networks"].items()
    ]


@mcp.tool()
def lookup_reason_code(network: str, code: str) -> dict[str, Any]:
    """Look up a single reason code on a given network (visa, mastercard, amex)."""
    net = _network(network)
    if code not in net["reason_codes"]:
        available = ", ".join(sorted(net["reason_codes"].keys()))
        raise ValueError(f"Code {code} not found for {net['name']}. Available: {available}")
    rc = net["reason_codes"][code]
    evidence = RULES["evidence_matrix"].get(rc["category"], [])
    return {
        "network": net["name"],
        "framework": net["framework"],
        "code": code,
        "title": rc["title"],
        "category": rc["category"],
        "time_limit_days": rc.get("time_limit_days"),
        "requires_pre_arbitration": rc.get("requires_pre_arbitration", False),
        "evidence_checklist": evidence,
        "source_ref": net["source"],
    }


@mcp.tool()
def search_rules(query: str, network: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    """Search reason codes by keyword in title. Optionally filter by network and category."""
    q = query.lower().strip()
    hits: list[dict[str, Any]] = []
    nets = [network.lower()] if network else list(RULES["networks"].keys())
    for net_key in nets:
        if net_key not in RULES["networks"]:
            continue
        net = RULES["networks"][net_key]
        for code, rc in net["reason_codes"].items():
            if category and rc["category"] != category:
                continue
            if q in rc["title"].lower() or q in code.lower() or q in rc["category"]:
                hits.append({
                    "network": net["name"],
                    "code": code,
                    "title": rc["title"],
                    "category": rc["category"],
                    "time_limit_days": rc.get("time_limit_days"),
                })
    return hits


@mcp.tool()
def get_evidence_checklist(category: str) -> list[str]:
    """Return evidence items typically needed to defend a dispute of a given category.

    Categories: fraud, authorization, processing_error, consumer_dispute.
    """
    if category not in RULES["evidence_matrix"]:
        raise ValueError(f"Unknown category: {category}. Use: {list(RULES['evidence_matrix'].keys())}")
    return RULES["evidence_matrix"][category]


@mcp.tool()
def compare_networks(scenario_category: str) -> dict[str, Any]:
    """Compare how the three networks handle a scenario category.

    scenario_category matches a Q&A template key (e.g., 'not_received',
    'cancelled_recurring', 'duplicate', 'fraud_cnp').
    """
    matches = [c for c in CONTEXTS if c["category"] == scenario_category and c["network"] == "comparison"]
    if not matches:
        available = sorted({c["category"] for c in CONTEXTS})
        raise ValueError(f"No comparison for '{scenario_category}'. Try one of: {available}")
    return matches[0]["answer"]


@mcp.tool()
def answer_question(question: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Return the top_k pre-computed Q&A contexts most similar to `question` by keyword overlap."""
    q_tokens = {t for t in question.lower().split() if len(t) > 2}
    scored: list[tuple[int, dict[str, Any]]] = []
    for ctx in CONTEXTS:
        c_tokens = {t for t in ctx["question"].lower().split() if len(t) > 2}
        score = len(q_tokens & c_tokens)
        if score:
            scored.append((score, ctx))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [c for _, c in scored[:top_k]]


@mcp.resource("chargeback://networks")
def networks_resource() -> str:
    """All supported networks, their frameworks, and source PDFs."""
    return json.dumps(list_networks(), indent=2)


@mcp.resource("chargeback://contexts")
def contexts_resource() -> str:
    """All 100 pre-extracted Q&A contexts."""
    return json.dumps(CONTEXTS, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
