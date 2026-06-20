import json

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.llm.prompts import EVALUATOR_SYSTEM_PROMPT
from app.llm.schemas import EVALUATION_SCHEMA

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def evaluate_decision_with_llm(
    scenario: dict,
    session: dict,
    user_decision: str,
    reference_cases: list,
) -> dict:
    user_prompt = f"""
Scenario:
{json.dumps(scenario, ensure_ascii=False, indent=2)}

Current session:
{json.dumps(session, ensure_ascii=False, indent=2)}

User decision:
{user_decision}

Relevant reference cases:
{json.dumps(reference_cases, ensure_ascii=False, indent=2)}

Evaluate this decision and produce the next crisis state.
"""
    response = get_client().responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": EVALUATION_SCHEMA["name"],
                "schema": EVALUATION_SCHEMA["schema"],
                "strict": True,
            }
        },
    )
    return json.loads(response.output_text)
