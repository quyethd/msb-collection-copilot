from __future__ import annotations

from typing import Any

from .errors import ToolFailure, invalid
from .repository import ToolRepository

ROUTES = {"CALL", "CBS", "OTHER"}
MOVEMENTS = {"PROMOTED", "DEMOTED", "UNCHANGED"}
EVENT_TYPES = {"CALL", "OPERATION", "PAYMENT", "PTP"}


def _cif(arguments: dict[str, Any], repository: ToolRepository) -> str:
    value = arguments.get("cif")
    if not isinstance(value, str) or not value.strip():
        raise invalid("cif must be a non-blank string")
    if value not in repository.cifs:
        raise ToolFailure("NOT_FOUND", f"CIF {value!r} was not found")
    return value


def _limit(arguments: dict[str, Any], default: int = 20) -> int:
    value = arguments.get("limit", default)
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise invalid("limit must be an integer from 1 through 100")
    return value


def get_portfolio(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    allowed = {"limit", "offset", "final_route", "movement", "hard_suppressed"}
    unknown = set(arguments) - allowed
    if unknown:
        raise invalid(f"unknown argument(s): {sorted(unknown)}")
    limit = _limit(arguments)
    offset = arguments.get("offset", 0)
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise invalid("offset must be a non-negative integer")
    route, movement, suppressed = (arguments.get(k) for k in ("final_route", "movement", "hard_suppressed"))
    if route is not None and route not in ROUTES:
        raise invalid(f"final_route must be one of {sorted(ROUTES)}")
    if movement is not None and movement not in MOVEMENTS:
        raise invalid(f"movement must be one of {sorted(MOVEMENTS)}")
    if suppressed is not None and not isinstance(suppressed, bool):
        raise invalid("hard_suppressed must be boolean")
    rows = repository.portfolio()
    if route is not None: rows = [row for row in rows if row["final_route"] == route]
    if movement is not None: rows = [row for row in rows if row["movement"] == movement]
    if suppressed is not None: rows = [row for row in rows if row["hard_suppressed"] is suppressed]
    return {"items": rows[offset:offset + limit], "total_matching": len(rows), "limit": limit,
            "offset": offset, **repository.meta}


def get_customer_360(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    return repository.context(_only_cif(arguments, repository))


def _only_cif(arguments: dict[str, Any], repository: ToolRepository) -> str:
    unknown = set(arguments) - {"cif"}
    if unknown: raise invalid(f"unknown argument(s): {sorted(unknown)}")
    return _cif(arguments, repository)


def get_collection_history(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    unknown = set(arguments) - {"cif", "event_types", "limit"}
    if unknown: raise invalid(f"unknown argument(s): {sorted(unknown)}")
    cif, limit = _cif(arguments, repository), _limit(arguments)
    requested = arguments.get("event_types", sorted(EVENT_TYPES))
    if (not isinstance(requested, list) or not requested
            or any(not isinstance(x, str) or x not in EVENT_TYPES for x in requested)
            or len(requested) != len(set(requested))):
        raise invalid(f"event_types must be a non-empty list containing only {sorted(EVENT_TYPES)}")
    requested_set = set(requested)
    events: list[dict[str, Any]] = []
    for row in repository.source_events("CALL"):
        if row["cif"] == cif and "CALL" in requested_set:
            events.append({"event_type": "CALL", "source_id": row["id"], "event_timestamp": row["call_time"], "payload": row})
    for row in repository.source_events("PAYMENT"):
        if row["cif"] == cif and "PAYMENT" in requested_set:
            events.append({"event_type": "PAYMENT", "source_id": row["payment_id"], "event_timestamp": row["payment_date"], "payload": row})
    for row in repository.source_events("OPERATION"):
        if row["cif"] != cif: continue
        kind = "PTP" if row["operation_result"] == "PTP" else "OPERATION"
        if kind in requested_set:
            events.append({"event_type": kind, "source_id": row["id"], "event_timestamp": row["created_at"], "payload": row})
    events.sort(key=lambda row: row["source_id"])
    events.sort(key=lambda row: row["event_timestamp"], reverse=True)
    return {"cif": cif, "events": events[:limit], "total_matching": len(events), "limit": limit,
            "ptp_mapping": "PTP labels source OPERATION rows whose operation_result is PTP; events are not duplicated."}


def get_cashflow_intelligence(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    context = repository.context(_only_cif(arguments, repository))
    return {"cif": context["cif"], "cashflow_available": context["availability"]["cashflow_available"],
            **context["cashflow"], "scoring_evidence": context["evidence"]["cashflow"],
            "accepted_rule_ids": [row["rule_id"] for row in context["evidence"]["cashflow"]]}


def get_collection_policy(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    context = repository.context(_only_cif(arguments, repository))
    return {"cif": context["cif"], **context["policy"]}


def get_recovery_opportunity(arguments: dict[str, Any], repository: ToolRepository) -> dict[str, Any]:
    context = repository.context(_only_cif(arguments, repository))
    return {"cif": context["cif"], **context["recovery_opportunity"], **context["ranking"],
            "score_semantics": "Explainable prototype prioritization score; not probability of payment or cure, expected recovery, or expected monetary value."}
