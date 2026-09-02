from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from msb_context.assembler import ContextAssemblyError, ContextNotFoundError, DecisionContextStore, _recent, assemble, assemble_directory
from msb_context.io import load_contexts, portfolio_index, write_artifacts
from msb_context.models import SYNTHETIC_LABEL
from msb_context.validate import FORBIDDEN_OUTPUT_KEYS, _keys, validate, validate_persisted
from msb_evaluation.io import evaluate_directory as evaluate_evaluation_directory
from msb_policy.io import evaluate_directory as evaluate_policy_directory, read_csv
from msb_recovery.io import evaluate_directory as evaluate_recovery_directory
from msb_synthetic.generator import generate_to


def tree_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.iterdir() if item.is_file()):
        digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


class ContextAssemblyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name); cls.data = cls.root / "data"
        generate_to(cls.data)
        cls.source_hash = tree_hash(cls.data)
        cls.contexts = assemble_directory(cls.data)
        cls.by_cif = {row.cif: row for row in cls.contexts}
        cls.report = validate(cls.data, cls.contexts)
        cls.out_a, cls.out_b = cls.root / "out-a", cls.root / "out-b"
        write_artifacts(cls.contexts, cls.report, cls.out_a)
        contexts_again = assemble_directory(cls.data)
        write_artifacts(contexts_again, validate(cls.data, contexts_again), cls.out_b)
        for output in (cls.out_a, cls.out_b):
            persisted_report = validate_persisted(cls.data, output)
            (output / "golden_context_validation.json").write_text(json.dumps(persisted_report, indent=2, sort_keys=True) + "\n")

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_join_integrity_and_version_date(self):
        self.assertEqual((len(self.contexts), len(self.by_cif)), (3000, 3000))
        self.assertTrue(all(row.context_version == "1.0" and row.as_of_date == "2026-08-28" for row in self.contexts))
        self.assertEqual(self.report["duplicate_context_cif"], 0)
        self.assertEqual(self.report["missing_context_cif"], 0)
        self.assertEqual(self.report["unexpected_context_cif"], 0)

    def test_authoritative_stage_cif_mismatch_fails(self):
        customers = read_csv(self.data, "customer"); loans = read_csv(self.data, "loan_account")
        cash = read_csv(self.data, "cashflow_transaction"); payments = read_csv(self.data, "payment_event")
        calls = read_csv(self.data, "call_history"); operations = read_csv(self.data, "operation_result")
        policies = evaluate_policy_directory(self.data); recoveries = evaluate_recovery_directory(self.data)
        evaluations, _ = evaluate_evaluation_directory(self.data)
        args = (customers, loans, cash, payments, calls, operations, policies, recoveries)
        with self.assertRaises(ContextAssemblyError): assemble(*args, evaluations[:-1], "2026-08-28")
        with self.assertRaises(ContextAssemblyError): assemble(*args[:-1], recoveries + [replace(recoveries[0], cif="UNEXPECTED")], evaluations, "2026-08-28")

    def test_debt_consistency_and_g20(self):
        for row in self.contexts:
            self.assertEqual(row.debt["total_outstanding_cif"], sum(int(loan["outstanding_amount"]) for loan in row.debt["loans"]))
            self.assertEqual(row.debt["max_dpd_cif"], max(int(loan["dpd"]) for loan in row.debt["loans"]))
        g20 = self.by_cif["GOLDEN_G20"]
        self.assertEqual((g20.debt["loan_count"], g20.debt["total_outstanding_cif"], g20.debt["max_dpd_cif"]), (3, 400_000_000, 12))
        self.assertEqual([(int(row["outstanding_amount"]), int(row["dpd"])) for row in g20.debt["loans"]], [(100_000_000, 4), (250_000_000, 12), (50_000_000, 7)])

    def test_upstream_immutability(self):
        self.assertEqual(self.report["task2_authoritative_mismatches"], 0)
        self.assertEqual(self.report["task3_authoritative_mismatches"], 0)
        self.assertEqual(self.report["task4_authoritative_mismatches"], 0)

    def test_missing_is_distinct_from_actual_zero(self):
        g01 = self.by_cif["GOLDEN_G01"]
        self.assertFalse(g01.availability["cashflow_available"])
        for field in (
            "inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d",
            "net_cashflow_30d", "income_sources_30d", "net_cashflow_windows_30d",
            "positive_cashflow_windows", "liquidity_to_due_ratio",
        ):
            self.assertIsNone(g01.cashflow[field])
        self.assertEqual(g01.cashflow["recent_transactions"], [])
        available_zero = next(
            row for row in self.contexts
            if row.availability["cashflow_available"]
            and row.cashflow["inflow_3d"] == 0
            and row.cashflow["positive_cashflow_windows"] == 0
        )
        self.assertTrue(available_zero.availability["cashflow_available"])
        self.assertEqual(available_zero.cashflow["inflow_3d"], 0)
        self.assertEqual(available_zero.cashflow["positive_cashflow_windows"], 0)
        self.assertIsNone(self.by_cif["GOLDEN_G19"].ptp["status"])
        self.assertFalse(self.by_cif["GOLDEN_G19"].availability["ptp_available"])

    def test_equal_timestamp_uses_source_id_ascending_tie_break(self):
        rows = [
            {"transaction_date": "2026-08-28T08:00:00+00:00", "transaction_id": "TXN-002"},
            {"transaction_date": "2026-08-27T08:00:00+00:00", "transaction_id": "TXN-003"},
            {"transaction_date": "2026-08-28T08:00:00+00:00", "transaction_id": "TXN-001"},
        ]
        ordered = _recent(rows, "transaction_date", "transaction_id", 10)
        self.assertEqual([row["transaction_id"] for row in ordered], ["TXN-001", "TXN-002", "TXN-003"])

        customers = read_csv(self.data, "customer"); loans = read_csv(self.data, "loan_account")
        cash = read_csv(self.data, "cashflow_transaction"); payments = read_csv(self.data, "payment_event")
        calls = read_csv(self.data, "call_history"); operations = read_csv(self.data, "operation_result")
        policies = evaluate_policy_directory(self.data); recoveries = evaluate_recovery_directory(self.data)
        evaluations, _ = evaluate_evaluation_directory(self.data)
        timestamp = "2026-08-29T08:00:00+00:00"
        template = next(row for row in cash if row["cif"] == "GOLDEN_G02")
        additions = [dict(template, transaction_id=source_id, transaction_date=timestamp) for source_id in ("ZZZ-TIE", "AAA-TIE")]
        assembled = assemble(customers, loans, cash + additions, payments, calls, operations, policies, recoveries, evaluations, "2026-08-28")
        g02 = next(row for row in assembled if row.cif == "GOLDEN_G02")
        self.assertEqual([row["transaction_id"] for row in g02.cashflow["recent_transactions"][:2]], ["AAA-TIE", "ZZZ-TIE"])

    def test_human_and_technical_boundaries(self):
        g02 = self.by_cif["GOLDEN_G02"]
        self.assertEqual(g02.ptp["employee_assessed_ability"], "HIGH")
        self.assertIn("scoring_fulfillment_ratio_raw", g02.ptp)
        g19 = self.by_cif["GOLDEN_G19"]
        self.assertGreater(g19.contact["technical_call_status_counts"]["Success"], 0)
        self.assertIsNone(g19.ptp["status"])
        self.assertEqual(g19.recovery_opportunity["willingness_to_pay_score"], 0)

    def test_overpayment_preserves_capped_and_raw_ratios(self):
        policies = evaluate_policy_directory(self.data)
        recoveries = evaluate_recovery_directory(self.data)
        policy = next(row for row in policies if row.cif == "GOLDEN_G09")
        recovery = next(row for row in recoveries if row.cif == "GOLDEN_G09")
        updated_features = dict(recovery.derived_features, ptp_fulfillment_ratio=Decimal("1.25"))
        policies[policies.index(policy)] = replace(policy, actual_paid_amount=Decimal(25_000_000), fulfillment_ratio=Decimal(1))
        recoveries[recoveries.index(recovery)] = replace(recovery, derived_features=updated_features)
        evaluations, _ = evaluate_evaluation_directory(self.data)
        context = next(row for row in assemble(
            read_csv(self.data, "customer"), read_csv(self.data, "loan_account"),
            read_csv(self.data, "cashflow_transaction"), read_csv(self.data, "payment_event"),
            read_csv(self.data, "call_history"), read_csv(self.data, "operation_result"),
            policies, recoveries, evaluations, "2026-08-28",
        ) if row.cif == "GOLDEN_G09")
        self.assertGreater(context.ptp["actual_paid_amount"], context.ptp["promise_amount"])
        self.assertEqual(context.ptp["policy_fulfillment_ratio"], Decimal(1))
        self.assertEqual(context.ptp["scoring_fulfillment_ratio_raw"], Decimal("1.25"))

    def test_previews_are_bounded_and_ordered(self):
        self.assertEqual(self.report["preview_limit_violations"], 0)
        self.assertEqual(self.report["preview_ordering_violations"], 0)
        self.assertTrue(any(len(row.cashflow["recent_transactions"]) == 10 for row in self.contexts))

    def test_index_complete_and_recovery_sorted(self):
        index = portfolio_index(self.contexts)
        required_fields = {
            "cif", "final_route", "hard_suppressed", "total_outstanding_cif", "max_dpd_cif",
            "baseline_rank", "recovery_rank", "rank_delta", "movement",
            "recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score",
            "willingness_to_pay_score", "contactability_score", "timing_opportunity_score",
            "strategic_adjustment_score", "availability",
        }
        self.assertEqual(len(index), 3000)
        self.assertEqual({row["cif"] for row in index}, set(self.by_cif))
        self.assertTrue(all(required_fields <= set(row) for row in index))
        self.assertEqual([row["recovery_rank"] for row in index], list(range(1, 3001)))

    def test_lookup(self):
        store = DecisionContextStore(self.contexts)
        serialized = {row["cif"]: row for row in load_contexts(self.out_a / "customer_context.jsonl")}
        self.assertEqual(store.get_customer_context("GOLDEN_G02").to_dict(), serialized["GOLDEN_G02"])
        with self.assertRaises(ContextNotFoundError): store.get_customer_context("UNKNOWN")

    def test_golden_contexts_and_truthful_statuses(self):
        self.assertEqual(self.report["status"], "PASS", self.report["errors"])
        self.assertEqual({sid for sid, status in self.report["golden"].items() if status == "PASS"}, {"G01", "G02", "G04", "G07", "G08", "G19", "G20"})
        self.assertEqual(self.by_cif["GOLDEN_G01"].ranking["movement"], "DEMOTED")
        self.assertEqual(self.by_cif["GOLDEN_G02"].ranking["movement"], "PROMOTED")
        self.assertEqual(self.by_cif["GOLDEN_G04"].ptp["status"], "BROKEN")
        self.assertEqual((self.by_cif["GOLDEN_G07"].policy["final_route"], self.by_cif["GOLDEN_G08"].policy["final_route"]), ("CALL", "CBS"))

    def test_provenance_and_forbidden_fields(self):
        self.assertTrue(all(row.provenance["synthetic_data"] and row.provenance["synthetic_label"] == SYNTHETIC_LABEL for row in self.contexts))
        self.assertFalse(set().union(*(_keys(row.to_dict()) for row in self.contexts)) & FORBIDDEN_OUTPUT_KEYS)

    def test_serialized_schema_and_determinism(self):
        required = {"customer_context.jsonl", "portfolio_context_index.json", "golden_context_validation.json", "context_manifest.json"}
        self.assertEqual({path.name for path in self.out_a.iterdir()}, required)
        serialized = load_contexts(self.out_a / "customer_context.jsonl")
        self.assertEqual(len(serialized), 3000)
        self.assertTrue({"customer", "debt", "policy", "cashflow", "payment", "ptp", "contact", "recovery_opportunity", "ranking", "evidence", "availability", "provenance"} <= set(serialized[0]))
        index = json.loads((self.out_a / "portfolio_context_index.json").read_text())
        manifest = json.loads((self.out_a / "context_manifest.json").read_text())
        golden = json.loads((self.out_a / "golden_context_validation.json").read_text())
        self.assertEqual((len(index), manifest["customer_count"], golden["context_count"]), (3000, 3000, 3000))
        self.assertEqual((golden["persisted_artifacts_parsed"], golden["persisted_contexts_checked"], golden["persisted_schema_errors"], golden["missing_semantic_violations"]), (4, 3000, 0, 0))
        serialized_by_cif = {row["cif"]: row for row in serialized}
        missing = serialized_by_cif["GOLDEN_G01"]
        self.assertFalse(missing["availability"]["cashflow_available"])
        for field in (
            "inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d",
            "net_cashflow_30d", "income_sources_30d", "net_cashflow_windows_30d",
            "positive_cashflow_windows", "liquidity_to_due_ratio",
        ):
            self.assertIsNone(missing["cashflow"][field])
        self.assertEqual(missing["cashflow"]["recent_transactions"], [])
        available_zero = next(row for row in serialized if row["availability"]["cashflow_available"] and row["cashflow"]["inflow_3d"] == 0 and row["cashflow"]["positive_cashflow_windows"] == 0)
        self.assertEqual(available_zero["cashflow"]["inflow_3d"], 0)
        self.assertEqual(available_zero["cashflow"]["positive_cashflow_windows"], 0)
        for name in required:
            self.assertEqual((self.out_a / name).read_bytes(), (self.out_b / name).read_bytes())
        self.assertEqual(tree_hash(self.data), self.source_hash)


if __name__ == "__main__": unittest.main()
