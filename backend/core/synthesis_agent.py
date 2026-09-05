import json
import time
import hashlib
import os
from google.genai.errors import ClientError
from google import genai
from core.config import settings

CACHE_DIR = "core/.api_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(prompt: str) -> str:
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.json")


def _cached_call(prompt: str, fn):
    """Checks local disk cache before making a real API call — avoids
    burning free-tier daily quota on repeated test runs during dev."""
    path = _cache_path(prompt)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["text"]

    response = fn()
    text = response.text

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f)

    return text


def _call_with_retry(fn, max_retries: int = 3):
    """Retries on 429 rate-limit errors, waiting the delay the API suggests."""
    for attempt in range(max_retries):
        try:
            return fn()
        except ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) and attempt < max_retries - 1:
                wait_time = 30  # safe default if we can't parse the suggested delay
                print(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                raise

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-flash-lite-latest"


def _extract_json(text: str) -> str:
    """Strip markdown code fences that models often wrap JSON in."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def classify_comms_message(message_text: str) -> dict:
    """
    Comms Analyzer: decide if a message contains a technical
    decision or rationale worth correlating with code changes.
    """
    prompt = f"""You are analyzing a team chat message from a software engineering context.

Message: "{message_text}"

Does this message contain a technical decision, rationale, or explanation
for why something was built a certain way? Respond ONLY with valid JSON,
no other text, in this exact shape:

{{"is_decision": true or false, "summary": "one sentence summary if true, else empty string"}}
"""

    response_text = _cached_call(
        prompt,
        lambda: _call_with_retry(lambda: client.models.generate_content(model=MODEL_NAME, contents=prompt))
    )

    try:
        cleaned = _extract_json(response_text)
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError) as e:
        return {"is_decision": False, "summary": "", "error": str(e)}


def generate_adr(commit_diff: str, correlated_messages: list[str], commit_sha: str) -> dict:
    """
    Synthesis Agent: draft an ADR from a code change plus the
    team discussion that explains it.
    """
    messages_block = "\n".join(f"- {m}" for m in correlated_messages)

    prompt = f"""You are drafting a concise Architecture Decision Record (ADR)
based primarily on a team discussion, using a related code change as
supporting evidence only.

The team discussion below is the PRIMARY source — it states the actual
decision and rationale. Base the ADR's Decision and Rationale sections on
what the discussion says, in your own words. Do NOT invent a decision or
rationale from the diff alone if the discussion doesn't support it.

Team discussion (primary source):
{messages_block}

Related code change (supporting evidence only — reference it in the
Source section, don't let it drive the Decision/Rationale content):
{commit_diff}

Write a short ADR with three sections: Decision, Rationale, and Source.
Cite the commit SHA {commit_sha} in the Source section.
Respond ONLY with valid JSON in this exact shape:

{{"title": "short title", "content": "full ADR text with the three sections"}}
"""

    response_text = _cached_call(
        prompt,
        lambda: _call_with_retry(lambda: client.models.generate_content(model=MODEL_NAME, contents=prompt))
    )

    try:
        cleaned = _extract_json(response_text)
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError) as e:
        return {"title": "Generation failed", "content": "", "error": str(e)}