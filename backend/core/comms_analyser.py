import json
import os
import time

from sqlalchemy.orm import Session

from models.comms_message import CommsMessage
from core.synthesis_agent import classify_comms_message

CACHE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "comms_classification_cache.json")


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def analyze_comms(run_id: str, db: Session, messages: list[dict]) -> list[CommsMessage]:
    created_messages = []
    cache = _load_cache()

    for msg in messages:
        text = msg["text"]
        if text in cache:
            classification = cache[text]
        else:
            classification = classify_comms_message(text)
            cache[text] = classification
            _save_cache(cache)  # save after every live call, not just at the end
            time.sleep(13)

        comms_message = CommsMessage(
            run_id=run_id,
            author=msg.get("author"),
            text=text,
            timestamp=msg.get("timestamp"),
            is_decision=classification.get("is_decision", False),
            summary=classification.get("summary", ""),
        )
        db.add(comms_message)
        created_messages.append(comms_message)

    db.commit()
    return created_messages