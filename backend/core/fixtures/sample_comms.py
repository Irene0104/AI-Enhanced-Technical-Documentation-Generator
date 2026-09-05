"""
Fabricated Slack-style messages for demo/testing purposes only.
References real function/file names from the itsdangerous repo so the
Correlation Agent has something realistic to match against. Not real
team communications.
"""

from datetime import datetime, timedelta

BASE_TIME = datetime(2025, 6, 14, 10, 0, 0)

SAMPLE_COMMS_MESSAGES = [
    {
        "author": "alex",
        "text": "does anyone know why want_bytes silently returns None on some inputs? "
                "seeing weird failures downstream",
        "timestamp": BASE_TIME,
    },
    {
        "author": "jordan",
        "text": "yeah that's intentional — we return None instead of raising so callers can "
                "do their own fallback logic in base64_encode. changing it would break "
                "backwards compat for anyone relying on the current behavior",
        "timestamp": BASE_TIME + timedelta(minutes=12),
    },
    {
        "author": "sam",
        "text": "lunch?",
        "timestamp": BASE_TIME + timedelta(minutes=20),
    },
    {
        "author": "jordan",
        "text": "we decided to split BadSignature into its own exception instead of "
                "reusing BadData directly, so callers can catch signature failures "
                "specifically without catching every possible bad-data case",
        "timestamp": BASE_TIME + timedelta(hours=2),
    },
    {
        "author": "alex",
        "text": "makes sense, that's a much cleaner error hierarchy",
        "timestamp": BASE_TIME + timedelta(hours=2, minutes=3),
    },
    {
        "author": "priya",
        "text": "can someone review my PR when they get a sec",
        "timestamp": BASE_TIME + timedelta(hours=3),
    },
    {
        "author": "priya",
        "text": "went with int_to_bytes using a manual loop instead of int.to_bytes() "
                "directly because we still need to support older Python versions "
                "that don't have the built-in method",
        "timestamp": BASE_TIME + timedelta(hours=3, minutes=5),
    },
]