# Chargeback Rules MCP — Demo

MVP demo of a Model Context Protocol (MCP) server + Q&A app that answers
merchant / issuer / cardholder questions about Visa, Mastercard, and Amex
chargeback rules.

Assumptions for this demo:
- Original rule PDFs (Visa VCR, Mastercard MCCG, Amex Merchant Regulations)
  are served from an internal document server, referenced only by
  `internal://…` URIs in the data. No proprietary text is checked in.
- Rule content in `data/rules.json` is a paraphrased summary keyed by the
  publicly known reason-code numbers.

## Layout

```
chargeback-mcp/
├── server.py             # MCP server (stdio, FastMCP)
├── app.py                # standalone CLI demo (no MCP client needed)
├── build_contexts.py     # regenerates data/contexts.json
├── requirements.txt
└── data/
    ├── rules.json        # 48 reason codes across 3 networks + evidence matrix
    └── contexts.json     # 100 Q&A contexts (25 per network + 25 comparisons)
```

## Install

```
pip3 install -r requirements.txt
```

Only `server.py` needs the `mcp` package. `app.py` is pure stdlib.

## Try the demo CLI

```
python3 app.py stats
python3 app.py list
python3 app.py lookup visa 13.1
python3 app.py lookup mastercard 4837
python3 app.py lookup amex C08
python3 app.py compare not_received
python3 app.py ask "cardholder never received the item on Visa"
python3 app.py repl
```

## Run as an MCP server

```
python3 server.py
```

Wire the stdio transport into an MCP-capable client (Claude Desktop, an
IDE plugin, or your own harness). Advertised tools:

| Tool | Purpose |
|---|---|
| `list_networks` | Networks + framework + source PDF pointer |
| `lookup_reason_code(network, code)` | Full record for one code |
| `search_rules(query, network?, category?)` | Keyword search across codes |
| `get_evidence_checklist(category)` | Evidence items for defense |
| `compare_networks(scenario_category)` | Side-by-side across Visa/MC/Amex |
| `answer_question(question, top_k=3)` | Retrieve top-k pre-built Q&A contexts |

Resources: `chargeback://networks`, `chargeback://contexts`.

## Question-type coverage (25 categories × 4 = 100)

Fraud (CNP / CP / EMV / chip-PIN / does-not-recognize / questionable
merchant), authorization (none / declined / expired / amount-exceeds),
processing errors (late presentment / duplicate / paid-by-other-means /
incorrect amount / currency), consumer disputes (not received / services
not rendered / cancelled recurring / not as described / defective /
credit not processed / cancelled goods / goods returned /
misrepresentation / no-show hotel).

## Regenerating contexts

Edit `TEMPLATES` in `build_contexts.py`, then:

```
python3 build_contexts.py
```

## Notes / next steps

- Swap `data/rules.json` for a live loader that hits the internal PDF
  server and reruns extraction on schedule.
- Add a real retrieval layer (embeddings) in `answer_question` — the
  current keyword-overlap ranking is only for the demo.
- Add a second-presentment evidence bundler that fills PDF templates
  per network from the checklist.
