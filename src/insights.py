import json
from typing import Any

from google import genai
from google.genai import types

from src.db import _get_secret  

MODEL_NAME = "gemini-2.0-flash"

_SYSTEM_PROMPT = """You are a supply-chain analyst summarizing delivery KPIs \
for a Brazilian e-commerce operations team.

You will be given a JSON object of KPIs. Respond with ONLY a JSON object \
(no markdown fences, no preamble, no trailing commentary) matching exactly \
this shape:

{"bullets": ["...", "...", "..."], "risk_flag": "..."}

- "bullets": 3 to 5 short, plain-English, action-oriented takeaways that a \
non-technical ops manager could read and act on today. Reference the actual \
numbers given.
- "risk_flag": one short sentence naming the single biggest risk visible in \
the data, or the literal string "None -- metrics look stable." if nothing \
stands out.
"""


def _get_client() -> genai.Client:
    api_key = _get_secret("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Locally: add it to your .env file. "
            "On Streamlit Cloud: add it under your app's Settings -> Secrets."
        )
    return genai.Client(api_key=api_key)


def generate_insights(kpis: dict[str, Any]) -> dict:
    client = _get_client()

    prompt = f"KPIs:\n{json.dumps(kpis, indent=2, default=str)}"

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini response was not valid JSON: {raw_text[:200]!r}"
        ) from e

    bullets = result.get("bullets")
    if not isinstance(bullets, list) or not bullets:
        raise RuntimeError(f"Gemini response missing a non-empty 'bullets' list: {result}")

    return {
        "bullets": [str(b) for b in bullets],
        "risk_flag": str(result["risk_flag"]) if result.get("risk_flag") else None,
    }


if __name__ == "__main__":
    sample_kpis = {
        "overall_on_time_pct": 91.2,
        "avg_delay_days": -2.3,
        "worst_state": "AL",
        "worst_state_on_time_pct": 78.4,
        "total_orders": 96500,
        "late_rate_trend": "up 1.2pts vs previous month",
    }
    print(generate_insights(sample_kpis))