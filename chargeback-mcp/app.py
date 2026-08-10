"""Chargeback Q&A demo CLI.

Uses the same tool surface as server.py but runs standalone (no MCP client
needed) so you can eyeball answers quickly.

Usage:
    python3 app.py                              # interactive REPL
    python3 app.py ask "why was I double charged on Visa?"
    python3 app.py lookup visa 13.1
    python3 app.py compare not_received
    python3 app.py list
    python3 app.py stats
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RULES = json.loads((ROOT / "data" / "rules.json").read_text())
CONTEXTS = json.loads((ROOT / "data" / "contexts.json").read_text())


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_list(_args) -> None:
    for k, v in RULES["networks"].items():
        print(f"[{k}] {v['name']} — {v['framework']} — {len(v['reason_codes'])} codes")


def cmd_stats(_args) -> None:
    by_net: dict[str, int] = {}
    by_cat: dict[str, int] = {}
    for c in CONTEXTS:
        by_net[c["network"]] = by_net.get(c["network"], 0) + 1
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
    print(f"Total contexts: {len(CONTEXTS)}")
    print("By network:")
    for k, v in sorted(by_net.items()):
        print(f"  {k}: {v}")
    print(f"By category ({len(by_cat)} categories):")
    for k, v in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


def cmd_lookup(args) -> None:
    net_key = args.network.lower()
    net = RULES["networks"].get(net_key)
    if not net:
        print(f"Unknown network: {args.network}", file=sys.stderr)
        sys.exit(2)
    rc = net["reason_codes"].get(args.code)
    if not rc:
        print(f"Code {args.code} not found for {net['name']}", file=sys.stderr)
        sys.exit(2)
    _print({
        "network": net["name"],
        "framework": net["framework"],
        "code": args.code,
        "title": rc["title"],
        "category": rc["category"],
        "time_limit_days": rc.get("time_limit_days"),
        "requires_pre_arbitration": rc.get("requires_pre_arbitration", False),
        "evidence_checklist": RULES["evidence_matrix"].get(rc["category"], []),
        "source_ref": net["source"],
    })


def cmd_compare(args) -> None:
    matches = [c for c in CONTEXTS if c["category"] == args.category and c["network"] == "comparison"]
    if not matches:
        available = sorted({c["category"] for c in CONTEXTS})
        print(f"No comparison for '{args.category}'. Available:", file=sys.stderr)
        for a in available:
            print(f"  - {a}", file=sys.stderr)
        sys.exit(2)
    _print(matches[0]["answer"])


def _score(question: str, ctx: dict) -> int:
    q_tokens = {t for t in question.lower().split() if len(t) > 2}
    c_tokens = {t for t in ctx["question"].lower().split() if len(t) > 2}
    return len(q_tokens & c_tokens)


def cmd_ask(args) -> None:
    scored = [(_score(args.question, c), c) for c in CONTEXTS]
    scored = [(s, c) for s, c in scored if s > 0]
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    top = scored[: args.top_k]
    if not top:
        print("No matching context. Try different keywords or use `compare` / `lookup`.")
        return
    for score, ctx in top:
        print(f"--- {ctx['id']}  score={score}  network={ctx['network']}  category={ctx['category']}")
        print(f"Q: {ctx['question']}")
        print("A:")
        _print(ctx["answer"])
        print()


def cmd_repl(_args) -> None:
    print("Chargeback Q&A demo — type a question, or 'quit'.")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not q:
            continue
        if q.lower() in {"quit", "exit"}:
            return
        ns = argparse.Namespace(question=q, top_k=3)
        cmd_ask(ns)


def main() -> None:
    p = argparse.ArgumentParser(description="Chargeback rules demo CLI")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list").set_defaults(func=cmd_list)
    sub.add_parser("stats").set_defaults(func=cmd_stats)

    lp = sub.add_parser("lookup", help="Look up one reason code")
    lp.add_argument("network", choices=["visa", "mastercard", "amex"])
    lp.add_argument("code")
    lp.set_defaults(func=cmd_lookup)

    cp = sub.add_parser("compare", help="Compare networks for a scenario category")
    cp.add_argument("category")
    cp.set_defaults(func=cmd_compare)

    ap = sub.add_parser("ask", help="Ask a free-form question")
    ap.add_argument("question")
    ap.add_argument("--top-k", type=int, default=3, dest="top_k")
    ap.set_defaults(func=cmd_ask)

    sub.add_parser("repl", help="Interactive Q&A loop").set_defaults(func=cmd_repl)

    args = p.parse_args()
    if not getattr(args, "func", None):
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
