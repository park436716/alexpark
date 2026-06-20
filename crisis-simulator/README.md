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

## Run

```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload
```

`POST /api/sessions/start` with `{"case_id": "united_like"}` starts a session.
`POST /api/decisions/evaluate` evaluates a user decision and advances the
crisis phase.

## MVP scope

Included: 5 seed cases, choice + free-text decisions, LLM evaluation via
Structured Outputs, score deltas, stakeholder reactions, phase progression.

Not included yet: real-time news monitoring, multi-player workshops,
internal-document RAG, auto-generated press releases. See design notes for
the global crisis-case RAG layer (case fact / interpretation / playbook /
simulator layers) as the next phase.
