from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .registry import TOOL_REGISTRY, invoke_tool
from .repository import ToolRepository
from .schemas import schema_document, write_schema_artifacts

FORBIDDEN = {"treatment", "recommended_treatment", "next_best_action", "recommended_channel", "recommended_when", "best_contact_time", "action_priority", "expected_recovery", "expected_payment", "recovery_probability", "payment_probability", "cure_probability", "confidence_score", "agent_reasoning", "chain_of_thought", "ai_explanation", "model_explanation", "aev", "roi"}
READ_ONLY_TOOLS = {"get_portfolio", "get_customer_360", "get_collection_history", "get_cashflow_intelligence", "get_collection_policy", "get_recovery_opportunity"}
PUBLIC_TOOL_ALLOWLIST = frozenset({"get_customer_360", "get_next_best_action", "simulate_decision"})


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict): return set(value) | set().union(*(_keys(v) for v in value.values()), set())
    if isinstance(value, list): return set().union(*(_keys(v) for v in value), set())
    return set()


def tree_hash(directory: Path) -> str:
    """Hash accepted deterministic source semantics, excluding only generated_at."""
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.iterdir() if p.is_file()):
        content = path.read_bytes()
        if path.name == "generation_manifest.json":
            manifest = json.loads(content)
            manifest.pop("generated_at", None)
            content = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        digest.update(path.name.encode()); digest.update(content)
    return digest.hexdigest()


def validate(input_directory: Path) -> dict[str, Any]:
    before = tree_hash(input_directory); repo = ToolRepository(input_directory); errors: list[str] = []
    call = lambda name, args: invoke_tool(name, args, repository=repo)
    contexts = {cif: repo.context(cif) for cif in repo.cifs}
    portfolio = call("get_portfolio", {"limit": 100})
    if len(TOOL_REGISTRY) != 8: errors.append("registry count is not eight")
    if len(schema_document()["tools"]) != 8: errors.append("schema count is not eight")
    if len(repo.cifs) != 3000: errors.append("portfolio source does not contain 3,000 CIFs")
    invalids = [("get_portfolio", {"limit": 0}), ("get_portfolio", {"limit": 101}), ("get_portfolio", {"offset": -1}), ("get_portfolio", {"movement": "UP"}), ("get_collection_history", {"cif": "GOLDEN_G02", "event_types": ["SUCCESS"]}), ("get_collection_history", {"cif": "GOLDEN_G02", "event_types": ["CALL", "CALL"]}), ("get_customer_360", {"cif": ""})]
    failed_invalid = sum(not call(name, args)["ok"] for name, args in invalids)
    if failed_invalid != len(invalids): errors.append("an invalid input succeeded")
    mismatch = 0
    for row in repo.portfolio():
        c = contexts[row["cif"]]
        mismatch += row["final_route"] != c["policy"]["final_route"]
        mismatch += row["recovery_opportunity_score"] != c["recovery_opportunity"]["recovery_opportunity_score"]
        mismatch += row["recovery_rank"] != c["ranking"]["recovery_rank"]
    # Exercise the individual boundaries for every required Golden CIF too.
    for cif in ("GOLDEN_G01", "GOLDEN_G02", "GOLDEN_G04", "GOLDEN_G07", "GOLDEN_G08", "GOLDEN_G19", "GOLDEN_G20"):
        c = contexts[cif]; p = call("get_collection_policy", {"cif": cif})["data"]; r = call("get_recovery_opportunity", {"cif": cif})["data"]
        mismatch += p["final_route"] != c["policy"]["final_route"]
        mismatch += r["recovery_opportunity_score"] != c["recovery_opportunity"]["recovery_opportunity_score"]
        mismatch += r["recovery_rank"] != c["ranking"]["recovery_rank"]
    if mismatch: errors.append(f"cross-tool mismatches: {mismatch}")
    g = {name: contexts[f"GOLDEN_{name}"] for name in ("G01", "G02", "G04", "G07", "G08", "G19", "G20")}
    golden = {
        "G01": g["G01"]["ranking"]["baseline_rank"] == 1 and g["G01"]["ranking"]["recovery_rank"] == 917 and g["G01"]["recovery_opportunity"]["recovery_opportunity_score"] == 28 and call("get_cashflow_intelligence", {"cif": "GOLDEN_G01"})["data"]["inflow_3d"] is None,
        "G02": g["G02"]["ranking"]["baseline_rank"] == 1209 and g["G02"]["ranking"]["recovery_rank"] == 84 and g["G02"]["recovery_opportunity"]["recovery_opportunity_score"] == 58 and call("get_cashflow_intelligence", {"cif": "GOLDEN_G02"})["data"]["inflow_3d"] == 40_000_000,
        "G04": g["G04"]["ptp"]["status"] == "BROKEN" and g["G04"]["cashflow"]["inflow_3d"] > 0,
        "G07": (g["G07"]["policy"]["base_route"], g["G07"]["policy"]["challenge_override_route"], g["G07"]["policy"]["final_route"]) == ("CBS", "CALL", "CALL"),
        "G08": (g["G08"]["policy"]["base_route"], g["G08"]["policy"]["challenge_override_route"], g["G08"]["policy"]["final_route"]) == ("CALL", "CBS", "CBS"),
        "G19": g["G19"]["contact"]["technical_call_status_counts"].get("Success", 0) > 0 and g["G19"]["ptp"]["status"] is None and g["G19"]["recovery_opportunity"]["willingness_to_pay_score"] == 0,
        "G20": (g["G20"]["debt"]["loan_count"], g["G20"]["debt"]["total_outstanding_cif"], g["G20"]["debt"]["max_dpd_cif"]) == (3, 400_000_000, 12),
    }
    if not all(golden.values()): errors.append(f"golden failures: {[k for k,v in golden.items() if not v]}")
    sample_responses = [call(name, {} if name == "get_portfolio" else {"cif": "GOLDEN_G02"}) for name in TOOL_REGISTRY]
    readonly_responses = [row for name, row in zip(TOOL_REGISTRY, sample_responses) if name in READ_ONLY_TOOLS]
    forbidden = sorted(set().union(*(_keys(row) for row in readonly_responses)) & FORBIDDEN)
    if forbidden: errors.append(f"forbidden fields: {forbidden}")
    after = tree_hash(input_directory)
    if before != after: errors.append("source mutation detected")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "tool_count": len(TOOL_REGISTRY),
            "schema_tool_count": len(schema_document()["tools"]), "portfolio_cif_count": len(repo.cifs),
            "invalid_cases_tested": len(invalids), "invalid_cases_failed": failed_invalid,
            "cross_tool_mismatch_count": mismatch, "golden": {k: "PASS" if v else "FAIL" for k,v in golden.items()},
            "forbidden_fields": forbidden, "source_hash_before": before, "source_hash_after": after,
            "source_mutation": before != after, "reference_date": repo.reference_date}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate deterministic TASK-006 collection tools")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/tools/golden_tool_validation.json"))
    args = parser.parse_args(); report = validate(args.input)
    write_schema_artifacts(args.output.parent, report["reference_date"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
