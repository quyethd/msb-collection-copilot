from __future__ import annotations

import re
from typing import Any

from .models import MODES, Mode

_CIF_PATTERN = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b")

_PLAN_KEYWORDS = ("what should i do", "what should we do", "plan", "next action", "next best action", "recommend")
_EXPLAIN_KEYWORDS = ("why", "explain", "reason", "justification", "why did", "why was")
_INVESTIGATE_KEYWORDS = ("investigate", "tell me about", "what do we know", "what do you know", "show me", "facts", "details", "overview")
_SIMULATE_KEYWORDS = ("simulate", "what if", "what-if", "scenario", "hypothetical")


def extract_cif(message: Any) -> str | None:
    if not isinstance(message, str):
        return None
    match = _CIF_PATTERN.search(message)
    return match.group(0) if match else None


def infer_mode(message: Any, explicit: str | None = None) -> Mode:
    if isinstance(explicit, str) and explicit.upper() in MODES:
        return explicit.upper()  # type: ignore[return-value]
    text = message if isinstance(message, str) else ""
    lower = text.lower()
    if any(kw in lower for kw in _SIMULATE_KEYWORDS):
        return "SIMULATE"
    if any(kw in lower for kw in _EXPLAIN_KEYWORDS):
        return "EXPLAIN"
    if any(kw in lower for kw in _INVESTIGATE_KEYWORDS):
        return "INVESTIGATE"
    if any(kw in lower for kw in _PLAN_KEYWORDS):
        return "PLAN"
    return "PLAN"


def parse_payload(payload: dict[str, Any]) -> tuple[Mode, str | None, str | None]:
    mode = infer_mode(payload.get("message"), payload.get("mode"))
    cif = payload.get("cif")
    if not isinstance(cif, str) or not cif.strip():
        cif = extract_cif(payload.get("message"))
    else:
        cif = cif.strip()
    return mode, cif, payload.get("message")
