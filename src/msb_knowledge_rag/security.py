from __future__ import annotations

import re

_SENSITIVE_PATTERNS = (
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"passwd", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"bearer\s+", re.IGNORECASE),
    re.compile(r"reasoning[_-]?content", re.IGNORECASE),
    re.compile(r"chain[_-]?of[_-]?thought", re.IGNORECASE),
    re.compile(r"hidden[_-]?prompt", re.IGNORECASE),
    re.compile(r"\b\.env\b", re.IGNORECASE),
    re.compile(r"client[_-]?id", re.IGNORECASE),
    re.compile(r"client[_-]?secret", re.IGNORECASE),
)

_SENSITIVE_SIGNALS = (
    "api key",
    "api_key",
    "secret",
    "password",
    "passwd",
    "token",
    "credential",
    "client id",
    "client secret",
    "authorization",
    ".env",
    "sd đăng nhập",
    "reasoning_content",
    "chain of thought",
    "hidden prompt",
)


def security_scan(text: str) -> tuple[bool, str | None]:
    """Returns (blocked, reason) if the input looks like a secret-hunting query."""
    if not isinstance(text, str):
        return True, "non-text input blocked"
    lowered = text.lower()
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(lowered):
            return True, f"pattern {pattern.pattern!r}"
    for signal in _SENSITIVE_SIGNALS:
        if signal in lowered:
            return True, f"signal {signal!r}"
    return False, None


def redact_secrets(text: str) -> str:
    redacted = text
    redacted = re.sub(r"\b(?:LLM|GREENNODE|COLLECTION|IAM|MAAS|POS)_?API_?KEY\b[=: ]+\S+", "[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\bAPI_?KEY\b[=: ]+\S+", "[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"(Bearer\s+)\S+", r"\1[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted


def is_secret_word(word: str) -> bool:
    lowered = word.lower()
    return any(signal in lowered for signal in _SENSITIVE_SIGNALS)