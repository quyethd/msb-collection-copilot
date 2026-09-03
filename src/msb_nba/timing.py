from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from fractions import Fraction
from typing import Any, Iterable, Mapping

from .config import NBAConfig

BOUNDS = ((8, 10, "08-10"), (10, 12, "10-12"), (13, 15, "13-15"), (15, 17, "15-17"), (17, 19, "17-19"))


def _window(hour: int) -> str | None:
    return next((name for start, end, name in BOUNDS if start <= hour < end), None)


def select_best_window(calls: Iterable[Mapping[str, Any]], reference_date: date, config: NBAConfig) -> tuple[str, dict[str, Any]]:
    start = reference_date - timedelta(days=config.best_contact_lookback_days - 1)
    stats = defaultdict(lambda: [0, 0])
    for call in calls:
        if call.get("call_type") != "OUTBOUND" or not call.get("call_time"):
            continue
        timestamp = datetime.fromisoformat(str(call["call_time"]))
        if not start <= timestamp.date() <= reference_date:
            continue
        window = _window(timestamp.hour)
        if window is None:
            continue
        stats[window][0] += 1
        stats[window][1] += call.get("status") == "Success"
    details = {}
    for window in config.authorized_contact_windows:
        attempts, successes = stats[window]
        details[window] = {"attempt_count": attempts, "successful_call_count": successes,
                           "success_rate": None if attempts == 0 else f"{successes}/{attempts}"}
    historical = any(value[1] for value in stats.values())
    if not historical:
        selected = config.best_contact_fallback_window
    else:
        selected = max(config.authorized_contact_windows,
                       key=lambda w: (Fraction(stats[w][1], stats[w][0]) if stats[w][0] else Fraction(0), stats[w][1], -config.authorized_contact_windows.index(w)))
    return selected, {"source": "HISTORICAL" if historical else "FALLBACK", "lookback_start": start.isoformat(),
                      "lookback_end": reference_date.isoformat(), "windows": details}
