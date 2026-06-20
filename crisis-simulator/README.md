# AI Crisis Simulator (MVP)

A simulation engine that evaluates a user's crisis-response decisions against
real-world crisis cases and propagates the crisis state (reputation, legal
risk, media pressure, regulatory risk, employee trust, financial risk) across
phases (0h -> 6h -> 24h -> 72h -> 7d -> 30d).

This is not a chatbot. It's a state machine + LLM evaluator:

```
Scenario Engine -> Crisis State Machine -> Decision Interface
        -> AI Evaluator -> Stakeholder Simulator -> Score Engine
        -> Debrief Agent
```

## Structure

```
crisis-simulator/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entrypoint
│       ├── models/               # Pydantic models
│       ├── services/             # state machine, scoring, evaluator, scenario gen
│       ├── llm/                  # OpenAI client, prompts, JSON schema
│       ├── data/                 # seed case YAML (us_cases.yaml)
│       └── api/                  # FastAPI routers
└── frontend/
    └── components/                # React components (score board, etc.)
```

## Setup (step by step)

### 1. Python check

You need Python 3.10+.

```bash
python3 --version
```

### 2. Create an isolated virtual environment

Keeps this project's packages separate from anything else on your machine.

```bash
cd crisis-simulator/backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

You'll see `(venv)` appear in your prompt — that means it's active.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs `fastapi`, `uvicorn` (the server), `pydantic` (data
validation), `openai` (LLM client), `pyyaml` (reads `us_cases.yaml`).

### 4. Set your OpenAI API key

Copy `.env.example` to `.env` for reference, then export the real key in
your shell before starting the server:

```bash
export OPENAI_API_KEY="sk-your-real-key"
```

Get a key at https://platform.openai.com/api-keys. Without a real key,
`/api/sessions/start` still works (no LLM call), but
`/api/decisions/evaluate` will fail since it calls OpenAI.

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

`--reload` restarts the server automatically when you edit code. You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 6. Verify it's alive

```bash
curl http://localhost:8000/
# {"status":"ok"}
```

This hits `main.py`'s `health_check()`.

### 7. Start a session (no API key needed)

```bash
curl -X POST "http://localhost:8000/api/sessions/start?case_id=united_like"
```

Returns a `scenario` (the crisis setup) and a `session` (starting scores:
reputation 70, legal_risk 30, media_pressure 40, employee_trust 60,
regulatory_risk 30, financial_risk 25). Save this response — you feed it
back into step 8.

### 8. Evaluate a decision (needs a real API key)

```bash
curl -X POST "http://localhost:8000/api/decisions/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": <paste the "scenario" object from step 7>,
    "session": <paste the "session" object from step 7>,
    "user_decision": "피해자에게 직접 사과하고 즉시 조사를 시작하겠습니다.",
    "reference_cases": [{"id": "united_2017", "key_lessons": ["Avoid operational jargon"]}]
  }'
```

This calls OpenAI (Structured Outputs, `app/llm/openai_client.py`), then
`app/services/scoring_engine.py` applies the returned deltas to the
scores, and `app/services/state_machine.py` advances the phase. The
response contains `evaluation` (scores, strengths/weaknesses, stakeholder
reactions) and `updated_session` (new scores/phase — feed this back in as
`session` for the next decision).

### 9. Interactive API docs

FastAPI auto-generates a UI for testing endpoints in the browser:

```
http://localhost:8000/docs
```

### 10. Stop the server

`Ctrl+C` in the terminal where `uvicorn` is running.

## What each file does

| File | Role |
|---|---|
| `app/main.py` | Creates the FastAPI app, wires up the two routers |
| `app/config.py` | Env vars, initial scores, phase list |
| `app/models/*.py` | Pydantic shapes for scenario/session/decision/score |
| `app/data/us_cases.yaml` | Reference real-world cases (Tylenol, United, Starbucks, etc.) |
| `app/services/scenario_generator.py` | Returns a static demo scenario by `case_id` |
| `app/services/state_machine.py` | `get_next_phase()` — walks the phase list |
| `app/services/scoring_engine.py` | Adds LLM-returned deltas to scores, clamps to 0-100 |
| `app/services/evaluator.py` | Orchestrates: call LLM → update scores → advance phase |
| `app/llm/schemas.py` | JSON Schema the LLM's output must match (Structured Outputs) |
| `app/llm/prompts.py` | System prompt defining how the LLM should evaluate |
| `app/llm/openai_client.py` | Builds the prompt, calls `client.responses.create()` |
| `app/api/sessions.py` | `POST /api/sessions/start` |
| `app/api/decisions.py` | `POST /api/decisions/evaluate` |

## MVP scope

Included: 5 seed cases, choice + free-text decisions, LLM evaluation via
Structured Outputs, score deltas, stakeholder reactions, phase progression.

Not included yet: real-time news monitoring, multi-player workshops,
internal-document RAG, auto-generated press releases. See design notes for
the global crisis-case RAG layer (case fact / interpretation / playbook /
simulator layers) as the next phase.
