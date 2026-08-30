from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_SEED = 20260828
DEFAULT_REFERENCE_DATE = date(2026, 8, 28)
GENERATOR_VERSION = "1.0.0"
TABLES = (
    "customer", "loan_account", "collection_assignment", "cashflow_transaction",
    "payment_event", "operation_result", "call_history", "golden_scenario_expected",
)

FIELDS: dict[str, list[str]] = {
    "customer": ["cif", "customer_name", "segment", "heatmap", "created_at"],
    "loan_account": ["account_id", "cif", "product_type", "outstanding_amount", "overdue_amount", "dpd", "due_amount", "due_date", "status"],
    "collection_assignment": ["id", "cif", "base_route", "challenge_override_route", "effective_route", "assignment_date"],
    "cashflow_transaction": ["transaction_id", "cif", "transaction_date", "direction", "amount", "source_type", "balance_after"],
    "payment_event": ["payment_id", "cif", "account_id", "payment_date", "amount", "payment_type", "linked_ptp_id"],
    "operation_result": ["id", "cif", "operation_object", "relation", "detail_relation", "operation_address", "operation_result", "payment_ptp_date", "payment_ptp_number", "payment_ptp_ability", "overall_customer_assessment", "overdue_reason", "detail_overdue_reason", "debt_solution", "detail_operation_content", "is_change_contact_info", "is_current_address", "is_current_phone_number", "next_action_date", "next_operation_channel", "new_phone_number", "need_investigation", "work_status", "income_status", "affected_repayment_source", "proposed_solution", "created_at", "created_by", "updated_at", "updated_by"],
    "call_history": ["id", "call_id", "call_time", "end_time", "employee_name", "extension", "call_phone", "relationship", "cif", "status", "ring_duration", "talk_duration", "call_type", "record_file", "customer_name", "created_at", "created_by", "updated_at", "updated_by", "request_code", "start_at", "pbx", "end_at", "destination_name", "operation_status", "operation_source"],
    "golden_scenario_expected": ["scenario_id", "cif", "hero", "input_fixture", "expected_route", "expected_treatment", "expected_channel", "expected_timing_class", "expected_priority_band", "must_trigger_rule_ids", "must_not_trigger_rule_ids", "expected_score_constraints", "rationale"],
}


def iso_dt(day: date, hour: int = 9) -> str:
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc).isoformat()


def golden_definitions(ref: date) -> list[dict[str, Any]]:
    """Locked input/expected metadata; treatment values are fixtures, not evaluated logic."""
    d = lambda n: (ref + timedelta(days=n)).isoformat()
    definitions = [
        ("G01", "CALL", "CONTACT", "CALL", "LOW", "high debt/high DPD with no meaningful inflow, three broken PTPs, and five UTC/fail attempts", ["ROUTE-001"], ["SELF-001"]),
        ("G02", "CALL", "PTP_FOLLOW_UP", "CALL", "HIGH", "moderate debt, 40M recent inflow, 15M PTP due today, best contact window 15-17", ["CASH-002", "PTP-001"], []),
        ("G03", "CALL", "WAIT_SELF_CURE", "NONE", "NORMAL", "CALL route remains unchanged for a stable-income historical quick-cure candidate", ["SELF-001", "SELF-002"], []),
        ("G04", "CALL", "PTP_RECOVERY", "CALL", "HIGH", "broken 20M PTP plus 35M recent inflow and good contactability", ["PTP-004", "TREAT-003"], ["PTP-002"]),
        ("G05", "CALL", "CONTACT", "CALL", "NORMAL", "immutable what-if base fixture with no recent inflow; override is +30M today", [], []),
        ("G06", "CBS", "REMIND", "ZALO", "NORMAL", "RED heatmap, YELLOW segment, DPD2, due soon, no challenge override", ["ROUTE-002"], ["ROUTE-003"]),
        ("G07", "CALL", "CONTACT", "CALL", "NORMAL", "explicit synthetic CBS to CALL challenge override", ["ROUTE-003", "ROUTE-004"], []),
        ("G08", "CBS", "REMIND", "SMS", "NORMAL", "explicit synthetic CALL to CBS challenge override", ["ROUTE-003", "ROUTE-004"], []),
        ("G09", "CALL", "CONTACT", "CALL", "NORMAL", "20M promise with actual payment at least 20M", ["PTP-002"], ["PTP-003", "PTP-004"]),
        ("G10", "CALL", "PARTIAL_PAYMENT", "CALL", "HIGH", "20M promise with 10M actual payment and fulfillment ratio 0.5", ["PTP-003", "TREAT-004"], ["PTP-002"]),
        ("G11", "CALL", "PTP_FOLLOW_UP", "CALL", "HIGH", "20M promise, zero paid, beyond configured one-day demo grace", ["PTP-004"], ["PTP-002", "PTP-003"]),
        ("G12", "CALL", "PTP_FOLLOW_UP", "CALL", "NORMAL", "future promise date with zero paid", ["PTP-001"], ["PTP-004"]),
        ("G13", "CALL", "VERIFY_CONTACT", "NONE", "HIGH", "latest business outcome NIN on known-invalid synthetic number", ["CONTACT-002", "TREAT-002"], []),
        ("G14", "CALL", "CALLBACK", "CALL", "EXPLICIT", "NA with next action tomorrow and CALL channel", ["CONTACT-003", "TREAT-001"], []),
        ("G15", "CALL", "CONTACT", "CALL", "LOW", "five recent UTC outcomes demonstrate low contactability only", ["SCORE-CON-001"], []),
        ("G16", "CALL", "CONTACT", "CALL", "NORMAL", "recent RTP with good cashflow and technical call success separates ability from willingness", ["CASH-001", "SCORE-WIL-001"], []),
        ("G17", "CALL", "CONTACT", "CALL", "HIGH", "DPD35 with strong recent inflow and good contactability is not self-cure", ["SELF-003", "CASH-002"], ["SELF-001"]),
        ("G18", "CALL", "WAIT_SELF_CURE", "NONE", "NORMAL", "CALL-eligible low DPD with prior quick cures, stable income, no broken PTP or RTP", ["SELF-001", "SELF-002"], []),
        ("G19", "CALL", "CONTACT", "CALL", "NORMAL", "technical Success with talk time and no PTP business outcome", ["OUTCOME-003"], ["PTP-001", "PTP-002", "PTP-003", "PTP-004"]),
        ("G20", "CALL", "CONTACT", "CALL", "NORMAL", "three loans aggregate exactly to 400M outstanding and MAX DPD12", ["AGG-001", "AGG-002"], []),
    ]
    result = []
    for sid, route, treatment, channel, timing, rationale, trigger, forbidden in definitions:
        fixture: dict[str, Any] = {"reference_date": ref.isoformat()}
        if sid == "G05": fixture["simulation_override"] = {"cashflow_inflow_today": 30_000_000, "source_must_remain_unchanged": True}
        if sid == "G10": fixture.update({"promised_amount": 20_000_000, "actual_paid_amount": 10_000_000, "expected_ptp_status": "PARTIAL", "fulfillment_ratio": 0.5})
        if sid == "G20": fixture.update({"expected_total_outstanding": 400_000_000, "expected_max_dpd": 12})
        result.append({"scenario_id": sid, "cif": f"GOLDEN_{sid}", "hero": sid in {f"G0{i}" for i in range(1, 6)}, "input_fixture": fixture, "expected_route": route, "expected_treatment": treatment, "expected_channel": channel, "expected_timing_class": timing, "expected_priority_band": "CONFIGURABLE", "must_trigger_rule_ids": trigger, "must_not_trigger_rule_ids": forbidden, "expected_score_constraints": {}, "rationale": rationale})
    return result


class Generator:
    def __init__(self, seed: int, reference_date: date, population: int = 3000):
        if population < 20:
            raise ValueError("population must be at least 20 to contain G01-G20")
        self.seed, self.ref, self.population = seed, reference_date, population
        self.rng = random.Random(seed)
        self.rows: dict[str, list[dict[str, Any]]] = {name: [] for name in TABLES}
        self.accounts: dict[str, list[str]] = defaultdict(list)

    def add_customer(self, cif: str, idx: int, segment="ORANGE", heatmap="RED") -> None:
        self.rows["customer"].append({"cif": cif, "customer_name": f"SYNTHETIC CUSTOMER {idx:04d}", "segment": segment, "heatmap": heatmap, "created_at": iso_dt(self.ref - timedelta(days=365), 8)})

    def add_loan(self, cif: str, outstanding: int, dpd: int, suffix: int = 1) -> str:
        aid = f"SYN-LOAN-{cif}-{suffix:02d}"
        due = min(outstanding, max(500_000, outstanding // 10))
        self.rows["loan_account"].append({"account_id": aid, "cif": cif, "product_type": ("CREDIT_CARD", "PERSONAL_LOAN", "AUTO_LOAN")[suffix % 3], "outstanding_amount": outstanding, "overdue_amount": min(outstanding, due if dpd else 0), "dpd": dpd, "due_amount": due, "due_date": (self.ref - timedelta(days=dpd)).isoformat(), "status": "OVERDUE" if dpd else "CURRENT"})
        self.accounts[cif].append(aid)
        return aid

    def add_assignment(self, cif: str, base: str, override: str = "") -> None:
        self.rows["collection_assignment"].append({"id": f"SYN-ASG-{cif}", "cif": cif, "base_route": base, "challenge_override_route": override, "effective_route": override or base, "assignment_date": self.ref.isoformat()})

    def add_operation(self, cif: str, outcome: str, days: int, promised: int | str = "", promise_days: int | None = None, ability="MEDIUM", next_days: int | None = None, new_phone="") -> str:
        oid = f"SYN-OP-{len(self.rows['operation_result']) + 1:06d}"
        created = self.ref - timedelta(days=days)
        self.rows["operation_result"].append({"id": oid, "cif": cif, "operation_object": "CUSTOMER", "relation": "SELF", "detail_relation": "", "operation_address": "SYNTHETIC", "operation_result": outcome, "payment_ptp_date": (self.ref + timedelta(days=promise_days)).isoformat() if promise_days is not None else "", "payment_ptp_number": promised, "payment_ptp_ability": ability if outcome in {"PTP", "NPTP"} else "", "overall_customer_assessment": "SYNTHETIC ASSESSMENT", "overdue_reason": "SYNTHETIC REASON", "detail_overdue_reason": "", "debt_solution": "", "detail_operation_content": "SYNTHETIC FIXTURE", "is_change_contact_info": bool(new_phone), "is_current_address": True, "is_current_phone_number": outcome != "NIN", "next_action_date": iso_dt(self.ref + timedelta(days=next_days), 10) if next_days is not None else "", "next_operation_channel": "CALL" if next_days is not None else "", "new_phone_number": new_phone, "need_investigation": outcome == "NIN", "work_status": "EMPLOYED", "income_status": "STABLE", "affected_repayment_source": "", "proposed_solution": "", "created_at": iso_dt(created, 10), "created_by": "SYNTHETIC_GENERATOR", "updated_at": iso_dt(created, 10), "updated_by": "SYNTHETIC_GENERATOR"})
        return oid

    def add_call(self, cif: str, status: str, days: int, hour=10, talk: int | None = None, phone_suffix="") -> None:
        n = len(self.rows["call_history"]) + 1
        start = datetime.combine(self.ref - timedelta(days=days), datetime.min.time(), timezone.utc) + timedelta(hours=hour)
        talk = (120 if status == "Success" else 0) if talk is None else talk
        end = start + timedelta(seconds=10 + talk)
        self.rows["call_history"].append({"id": f"SYN-CALLROW-{n:06d}", "call_id": f"SYN-CALL-{n:06d}", "call_time": start.isoformat(), "end_time": end.isoformat(), "employee_name": "SYNTHETIC OFFICER", "extension": "SYN-EXT-01", "call_phone": f"SYN-PHONE-{cif}{phone_suffix}", "relationship": "SELF", "cif": cif, "status": status, "ring_duration": 10, "talk_duration": talk, "call_type": "OUTBOUND", "record_file": "", "customer_name": f"SYNTHETIC {cif}", "created_at": start.isoformat(), "created_by": "SYNTHETIC_GENERATOR", "updated_at": end.isoformat(), "updated_by": "SYNTHETIC_GENERATOR", "request_code": f"SYN-REQ-{n:06d}", "start_at": start.isoformat(), "pbx": "SYNTHETIC_PBX", "end_at": end.isoformat(), "destination_name": "SYNTHETIC DESTINATION", "operation_status": "", "operation_source": "SYNTHETIC"})

    def add_cash(self, cif: str, amount: int, days: int, direction="IN", source="TRANSFER", hour=8) -> None:
        n = len(self.rows["cashflow_transaction"]) + 1
        self.rows["cashflow_transaction"].append({"transaction_id": f"SYN-TXN-{n:07d}", "cif": cif, "transaction_date": iso_dt(self.ref - timedelta(days=days), hour), "direction": direction, "amount": amount, "source_type": source, "balance_after": max(amount // 2, 100_000)})

    def add_payment(self, cif: str, amount: int, days: int, linked="", payment_type="REGULAR") -> None:
        n = len(self.rows["payment_event"]) + 1
        self.rows["payment_event"].append({"payment_id": f"SYN-PAY-{n:06d}", "cif": cif, "account_id": self.accounts[cif][0], "payment_date": iso_dt(self.ref - timedelta(days=days), 14), "amount": amount, "payment_type": payment_type, "linked_ptp_id": linked})

    def golden(self) -> None:
        defs = golden_definitions(self.ref)
        dpds = {"G01": 65, "G02": 18, "G03": 5, "G04": 22, "G05": 15, "G06": 2, "G07": 2, "G08": 10, "G17": 35, "G18": 5}
        outstanding = {"G01": 500_000_000, "G02": 150_000_000, "G03": 80_000_000, "G04": 180_000_000, "G05": 120_000_000}
        for i, g in enumerate(defs, 1):
            sid, cif = g["scenario_id"], g["cif"]
            segment = "YELLOW" if sid in {"G06", "G07"} else "ORANGE"
            self.add_customer(cif, i, segment)
            if sid == "G20":
                for j, (amt, dpd) in enumerate(((100_000_000, 4), (250_000_000, 12), (50_000_000, 7)), 1): self.add_loan(cif, amt, dpd, j)
            else: self.add_loan(cif, outstanding.get(sid, 90_000_000), dpds.get(sid, 10))
            base = "CBS" if sid in {"G06", "G07"} else "CALL"
            override = "CALL" if sid == "G07" else ("CBS" if sid == "G08" else "")
            self.add_assignment(cif, base, override)
            g["input_fixture"].update({"base_route": base, "challenge_override_route": override or None, "effective_route": override or base, "dpd": dpds.get(sid, 10)})
            self.rows["golden_scenario_expected"].append(g)

        # Purpose-built evidence. PTP promise date is relative to evaluation date.
        for k in range(3): self.add_operation("GOLDEN_G01", "PTP", 8 + k, 10_000_000, -6 - k, "LOW")
        for k in range(5): self.add_operation("GOLDEN_G01", "UTC", k + 1); self.add_call("GOLDEN_G01", "No Answer", k + 1)
        op = self.add_operation("GOLDEN_G02", "PTP", 2, 15_000_000, 0, "HIGH")
        self.add_cash("GOLDEN_G02", 40_000_000, 1); self.add_call("GOLDEN_G02", "Success", 2, 16)
        for days in (90, 60, 30): self.add_cash("GOLDEN_G03", 25_000_000, days, source="SALARY"); self.add_payment("GOLDEN_G03", 5_000_000, max(1, days - 3), payment_type="SELF_CURE")
        op = self.add_operation("GOLDEN_G04", "PTP", 7, 20_000_000, -3, "HIGH"); self.add_cash("GOLDEN_G04", 35_000_000, 1); self.add_call("GOLDEN_G04", "Success", 1, 15)
        op = self.add_operation("GOLDEN_G09", "PTP", 5, 20_000_000, -2, "HIGH"); self.add_payment("GOLDEN_G09", 20_000_000, 1, op, "PTP_PAYMENT")
        op = self.add_operation("GOLDEN_G10", "PTP", 5, 20_000_000, -2, "MEDIUM"); self.add_payment("GOLDEN_G10", 10_000_000, 1, op, "PTP_PAYMENT")
        self.add_operation("GOLDEN_G11", "PTP", 6, 20_000_000, -3, "LOW")
        self.add_operation("GOLDEN_G12", "PTP", 1, 20_000_000, 3, "MEDIUM")
        self.add_operation("GOLDEN_G13", "NIN", 1); self.add_call("GOLDEN_G13", "No Answer", 1)
        self.add_operation("GOLDEN_G14", "NA", 1, next_days=1)
        for k in range(5): self.add_operation("GOLDEN_G15", "UTC", k + 1); self.add_call("GOLDEN_G15", "No Answer", k + 1)
        self.add_operation("GOLDEN_G16", "RTP", 1); self.add_cash("GOLDEN_G16", 30_000_000, 2); self.add_call("GOLDEN_G16", "Success", 1, talk=180)
        self.add_cash("GOLDEN_G17", 45_000_000, 1); self.add_call("GOLDEN_G17", "Success", 1, 14)
        for days in (90, 60, 30): self.add_cash("GOLDEN_G18", 22_000_000, days, source="SALARY"); self.add_payment("GOLDEN_G18", 4_000_000, max(1, days - 2), payment_type="SELF_CURE")
        self.add_call("GOLDEN_G19", "Success", 1, talk=150)

    def normal_population(self) -> None:
        for i in range(1, self.population - 19):
            cif = f"SYN{i:06d}"
            archetype = i % 6
            segment = ("RED", "ORANGE", "YELLOW", "GREEN")[i % 4]
            heatmap = "RED" if i % 5 else "AMBER"
            self.add_customer(cif, i + 20, segment, heatmap)
            loan_count = 1 + (i % 3 != 0) + (i % 10 == 0)
            for j in range(1, loan_count + 1):
                self.add_loan(cif, self.rng.randrange(5, 151) * 1_000_000, self.rng.randrange(0, 46), j)
            max_dpd = max(int(r["dpd"]) for r in self.rows["loan_account"][-loan_count:])
            eligible = heatmap == "RED" and segment in {"RED", "ORANGE", "YELLOW"}
            self.add_assignment(cif, "CALL" if eligible and max_dpd >= 5 else ("CBS" if eligible else "OTHER"))

        cifs = [r["cif"] for r in self.rows["customer"] if r["cif"].startswith("SYN")]
        # Stable, correlated monthly salary/business inflows plus ordinary outflows.
        while len(self.rows["cashflow_transaction"]) < 60_000:
            n = len(self.rows["cashflow_transaction"])
            cif = cifs[n % len(cifs)]; idx = int(cif[3:]); archetype = idx % 6
            days = (n // len(cifs)) * 4 + idx % 4
            if days > 89: days %= 90
            is_income = n % 5 == 0
            source = "SALARY" if is_income and archetype in {0, 2, 4} else ("BUSINESS_INCOME" if is_income else "OTHER")
            amount = (18_000_000 + idx % 8 * 1_000_000) if is_income else (200_000 + (idx * 7919 + n) % 2_800_000)
            self.add_cash(cif, amount, days, "IN" if is_income else "OUT", source)

        while len(self.rows["payment_event"]) < 12_000:
            n = len(self.rows["payment_event"]); cif = cifs[n % len(cifs)]
            self.add_payment(cif, 500_000 + n % 20 * 250_000, n % 120, payment_type="REGULAR")

        outcomes = ("UTC", "PTP", "NPTP", "RTP", "THIRT", "NA")
        while len(self.rows["operation_result"]) < 2_500:
            n = len(self.rows["operation_result"]); cif = cifs[n % len(cifs)]; outcome = outcomes[n % len(outcomes)]
            self.add_operation(cif, outcome, n % 30 + 1, 5_000_000 if outcome in {"PTP", "NPTP"} else "", 3 if outcome in {"PTP", "NPTP"} else None, ("CERTAIN", "HIGH", "MEDIUM", "LOW", "VERY_LOW")[n % 5], 2 if outcome == "NA" else None)

        while len(self.rows["call_history"]) < 6_500:
            n = len(self.rows["call_history"]); cif = cifs[n % len(cifs)]; high_contact = int(cif[3:]) % 6 in {1, 2}
            status = "Success" if high_contact and n % 3 else ("No Answer" if n % 2 else "Error SIP")
            self.add_call(cif, status, n % 30 + 1, 15 if high_contact else 10)

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        self.golden(); self.normal_population()
        return self.rows


def canonical_value(value: Any) -> str:
    if isinstance(value, (dict, list)): return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool): return "true" if value else "false"
    if value is None: return ""
    return str(value)


def write_dataset(rows: dict[str, list[dict[str, Any]]], output: Path, seed: int, ref: date) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    for table in TABLES:
        path = output / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, FIELDS[table], lineterminator="\n")
            writer.writeheader()
            for row in rows[table]:
                encoded = {key: canonical_value(row.get(key, "")) for key in FIELDS[table]}
                writer.writerow(encoded)
                digest.update((table + json.dumps(encoded, sort_keys=True, separators=(",", ":"))).encode())
    counts = {table: len(rows[table]) for table in TABLES}
    manifest = {"seed": seed, "reference_date": ref.isoformat(), "generator_version": GENERATOR_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(), "is_synthetic": True, "counts": counts, "golden_scenario_count": counts["golden_scenario_expected"], "hero_scenario_count": sum(bool(x["hero"]) for x in rows["golden_scenario_expected"]), "deterministic_digest": digest.hexdigest()}
    (output / "generation_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def generate_to(output: Path, seed=DEFAULT_SEED, reference_date=DEFAULT_REFERENCE_DATE, population=3000) -> dict[str, Any]:
    return write_dataset(Generator(seed, reference_date, population).generate(), output, seed, reference_date)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic, entirely synthetic collection data")
    parser.add_argument("--output", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--reference-date", type=date.fromisoformat, default=DEFAULT_REFERENCE_DATE)
    parser.add_argument("--population", type=int, default=3000)
    args = parser.parse_args()
    print(json.dumps(generate_to(args.output, args.seed, args.reference_date, args.population), indent=2, sort_keys=True))


if __name__ == "__main__": main()

