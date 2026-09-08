import json
from typing import Any
from google import genai
from src.db import _get_secret  

MODEL_NAME = "gemini-3.6-flash"

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
    """
    Summarize a dict of delivery KPIs into plain-English bullets plus a risk
    flag, using Gemini's Interactions API. Returns
    {"bullets": [str, ...], "risk_flag": str | None}.

    Raises RuntimeError if GEMINI_API_KEY is missing or Gemini's response
    can't be parsed as the expected JSON shape. Any underlying SDK/network
    error is left to propagate as-is so callers can distinguish "not
    configured" from "request failed".
    """
    client = _get_client()

    prompt = f"KPIs:\n{json.dumps(kpis, indent=2, default=str)}"

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        system_instruction=_SYSTEM_PROMPT,
        response_format={"type": "text", "mime_type": "application/json"},
        generation_config={"temperature": 0.2},
    )

    raw_text = (interaction.output_text or "").strip()
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