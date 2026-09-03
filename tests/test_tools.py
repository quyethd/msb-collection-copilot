from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from msb_context.assembler import assemble_directory
from msb_tools.registry import TOOL_REGISTRY, invoke_tool
from msb_tools.repository import ToolRepository
from msb_tools.schemas import registry_manifest, schema_document, write_schema_artifacts
from msb_tools.validate import FORBIDDEN, _keys, tree_hash, validate
from msb_synthetic.generator import generate_to


def _validate_schema_instance(value, schema, document, path="$"):
    """Focused validator for the JSON Schema features used by TASK-006 contracts."""
    while "$ref" in schema:
        target = document
        for part in schema["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        schema = target
    if "anyOf" in schema:
        if not any(_schema_matches(value, branch, document, path) for branch in schema["anyOf"]):
            raise AssertionError(f"{path}: no anyOf branch matched")
        return
    if "oneOf" in schema:
        matches = sum(_schema_matches(value, branch, document, path) for branch in schema["oneOf"])
        if matches != 1:
            raise AssertionError(f"{path}: expected exactly one oneOf branch, matched {matches}")
        return
    if "const" in schema and value != schema["const"]:
        raise AssertionError(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise AssertionError(f"{path}: value {value!r} not in enum")
    expected = schema.get("type")
    if expected:
        expected = [expected] if isinstance(expected, str) else expected
        matches = {"null": value is None, "object": isinstance(value, dict), "array": isinstance(value, list),
                   "string": isinstance(value, str),
                   "integer": isinstance(value, int) and not isinstance(value, bool),
                   "boolean": isinstance(value, bool)}
        if not any(matches.get(kind, False) for kind in expected):
            raise AssertionError(f"{path}: expected type {expected}, got {type(value).__name__}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise AssertionError(f"{path}: missing required property {key!r}")
        for key, item in value.items():
            if key in properties:
                _validate_schema_instance(item, properties[key], document, f"{path}.{key}")
            else:
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    raise AssertionError(f"{path}: unexpected property {key!r}")
                if isinstance(additional, dict):
                    _validate_schema_instance(item, additional, document, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate_schema_instance(item, schema["items"], document, f"{path}[{index}]")


def _schema_matches(value, schema, document, path):
    try:
        _validate_schema_instance(value, schema, document, path)
        return True
    except AssertionError:
        return False


class ToolLayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.root = Path(cls.temp.name)
        cls.data = cls.root / "data"; generate_to(cls.data)
        cls.repo = ToolRepository(cls.data); cls.contexts = {row.cif: row.to_dict() for row in assemble_directory(cls.data)}
        cls.call = staticmethod(lambda name, args: invoke_tool(name, args, repository=cls.repo))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_registry_exact(self):
        self.assertEqual(list(TOOL_REGISTRY), ["get_portfolio", "get_customer_360", "get_collection_history", "get_cashflow_intelligence", "get_collection_policy", "get_recovery_opportunity"])

    def test_unknown_tool_and_non_object_arguments(self):
        self.assertEqual(self.call("unknown", {})["error"]["code"], "INVALID_ARGUMENT")
        self.assertEqual(self.call("get_portfolio", [1])["error"]["code"], "INVALID_ARGUMENT")

    def test_schema_and_manifest_deterministic(self):
        self.assertEqual(json.dumps(schema_document(), sort_keys=True), json.dumps(schema_document(), sort_keys=True))
        self.assertEqual(registry_manifest("2026-08-28"), registry_manifest("2026-08-28"))
        self.assertEqual(len(schema_document()["tools"]), 6)

    def test_exported_output_schemas_are_meaningful(self):
        document = schema_document(); definitions = document["$defs"]
        expected = {
            "PortfolioOutput": ("items", "total_matching", "limit", "offset"),
            "Customer360Output": ("customer", "debt", "policy", "cashflow", "ranking", "provenance"),
            "CollectionHistoryOutput": ("events", "total_matching", "limit"),
            "CashflowIntelligenceOutput": ("cashflow_available", "inflow_3d", "liquidity_to_due_ratio"),
            "CollectionPolicyOutput": ("base_route", "challenge_override_route", "final_route"),
            "RecoveryOpportunityOutput": ("recovery_opportunity_score", "baseline_rank", "recovery_rank"),
        }
        for name, fields in expected.items():
            schema = definitions[name]
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])
            self.assertTrue(schema["required"])
            for field in fields:
                self.assertIn(field, schema["properties"])
                self.assertIn(field, schema["required"])
        portfolio_item = definitions["PortfolioOutput"]["properties"]["items"]["items"]
        self.assertIn("recovery_rank", portfolio_item["required"])
        self.assertIn("availability", portfolio_item["properties"])
        history_item = definitions["CollectionHistoryOutput"]["properties"]["events"]["items"]
        self.assertEqual(history_item["properties"]["payload"].get("oneOf") is not None, True)
        for field in ("inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d", "net_cashflow_30d"):
            self.assertIn("null", definitions["CashflowIntelligenceOutput"]["properties"][field]["type"])
        self.assertEqual(definitions["RecoveryOpportunityOutput"]["properties"]["recovery_opportunity_score"],
                         {"$ref": "#/$defs/RecoveryFacts/properties/recovery_opportunity_score"})

    def test_persisted_schema_matches_source_and_validates_responses(self):
        persisted_path = Path("build/tools/tool_schemas.json")
        self.assertTrue(persisted_path.is_file(), "persisted TASK-006 schema artifact is missing")
        persisted = json.loads(persisted_path.read_text(encoding="utf-8"))
        source = schema_document()
        self.assertEqual(persisted, source)
        output_schemas = {
            tool["name"]: persisted["$defs"][tool["output_schema"]["$ref"].split("/")[-1]]
            for tool in persisted["tools"]
        }
        samples = {
            "get_portfolio": {}, "get_customer_360": {"cif": "GOLDEN_G02"},
            "get_collection_history": {"cif": "GOLDEN_G02"},
            "get_cashflow_intelligence": {"cif": "GOLDEN_G02"},
            "get_collection_policy": {"cif": "GOLDEN_G02"},
            "get_recovery_opportunity": {"cif": "GOLDEN_G02"},
        }
        for tool_name, arguments in samples.items():
            data = self.call(tool_name, arguments)["data"]
            _validate_schema_instance(data, output_schemas[tool_name], persisted)

    def test_all_actual_tool_data_matches_exported_output_schemas(self):
        document = schema_document()
        output_schemas = {tool["name"]: document["$defs"][tool["output_schema"]["$ref"].split("/")[-1]]
                          for tool in document["tools"]}
        portfolio_rows = 0
        for offset in range(0, 3000, 100):
            data = self.call("get_portfolio", {"limit": 100, "offset": offset})["data"]
            _validate_schema_instance(data, output_schemas["get_portfolio"], document)
            portfolio_rows += len(data["items"])
            for row in data["items"]:
                self.assertEqual(row["synthetic_label"], "SYNTHETIC PROTOTYPE DATA")
        self.assertEqual(portfolio_rows, 3000)
        baseline_counts = {"AGG-001": 0, "AGG-002": 0}
        baseline_keys = {"AGG-001": {"rule_id", "total_outstanding_cif"},
                         "AGG-002": {"rule_id", "max_dpd_cif"}}
        for cif in sorted(self.repo.cifs):
            for tool_name in ("get_customer_360", "get_cashflow_intelligence",
                              "get_collection_policy", "get_recovery_opportunity"):
                data = self.call(tool_name, {"cif": cif})["data"]
                _validate_schema_instance(data, output_schemas[tool_name], document)
            for evidence in self.call("get_customer_360", {"cif": cif})["data"]["evidence"]["baseline"]:
                self.assertIn(evidence["rule_id"], baseline_counts)
                self.assertEqual(set(evidence), baseline_keys[evidence["rule_id"]])
                baseline_counts[evidence["rule_id"]] += 1
        self.assertEqual(baseline_counts, {"AGG-001": 3000, "AGG-002": 3000})
        for cif in ("GOLDEN_G01", "GOLDEN_G02", "GOLDEN_G04", "GOLDEN_G19", "GOLDEN_G20"):
            data = self.call("get_collection_history", {"cif": cif, "limit": 100})["data"]
            _validate_schema_instance(data, output_schemas["get_collection_history"], document)
        g20 = self.call("get_customer_360", {"cif": "GOLDEN_G20"})["data"]["evidence"]["baseline"]
        self.assertEqual(g20, [{"rule_id": "AGG-001", "total_outstanding_cif": 400_000_000},
                               {"rule_id": "AGG-002", "max_dpd_cif": 12}])

    def test_portfolio_limits_and_offset(self):
        self.assertEqual(len(self.call("get_portfolio", {})["data"]["items"]), 20)
        self.assertEqual(len(self.call("get_portfolio", {"limit": 1})["data"]["items"]), 1)
        self.assertEqual(len(self.call("get_portfolio", {"limit": 100})["data"]["items"]), 100)
        self.assertEqual(self.call("get_portfolio", {"offset": 4000})["data"]["items"], [])
        for args in ({"limit": 0}, {"limit": 101}, {"limit": True}, {"offset": -1}):
            self.assertEqual(self.call("get_portfolio", args)["error"]["code"], "INVALID_ARGUMENT")

    def test_portfolio_filters_and_order(self):
        for key, value in (("final_route", "CALL"), ("movement", "PROMOTED"), ("hard_suppressed", False)):
            rows = self.call("get_portfolio", {key: value, "limit": 100})["data"]["items"]
            self.assertTrue(rows and all(row[key] == value for row in rows))
        for args in ({"final_route": "EMAIL"}, {"movement": "UP"}, {"hard_suppressed": 1}, {"x": 1}):
            self.assertFalse(self.call("get_portfolio", args)["ok"])
        ranks = [row["recovery_rank"] for row in self.call("get_portfolio", {"limit": 100})["data"]["items"]]
        self.assertEqual(ranks, sorted(ranks))

    def test_customer_exact_and_validation(self):
        self.assertEqual(self.call("get_customer_360", {"cif": "GOLDEN_G02"})["data"], self.contexts["GOLDEN_G02"])
        self.assertEqual(self.call("get_customer_360", {"cif": "UNKNOWN"})["error"]["code"], "NOT_FOUND")
        self.assertEqual(self.call("get_customer_360", {"cif": " "})["error"]["code"], "INVALID_ARGUMENT")

    def test_history_order_limit_type_and_boundary(self):
        history = self.call("get_collection_history", {"cif": "GOLDEN_G02"})["data"]
        expected = sorted(history["events"], key=lambda row: row["source_id"])
        expected.sort(key=lambda row: row["event_timestamp"], reverse=True)
        self.assertEqual(history["events"], expected)
        self.assertEqual(len(self.call("get_collection_history", {"cif": "GOLDEN_G01", "limit": 1})["data"]["events"]), 1)
        self.assertFalse(self.call("get_collection_history", {"cif": "GOLDEN_G02", "event_types": ["SUCCESS"]})["ok"])
        for duplicate in (["CALL", "CALL"], ["PTP", "PTP"]):
            result = self.call("get_collection_history", {"cif": "GOLDEN_G02", "event_types": duplicate})
            self.assertFalse(result["ok"]); self.assertEqual(result["error"]["code"], "INVALID_ARGUMENT")
        calls = self.call("get_collection_history", {"cif": "GOLDEN_G19", "event_types": ["CALL"]})["data"]["events"]
        ptps = self.call("get_collection_history", {"cif": "GOLDEN_G19", "event_types": ["PTP"]})["data"]["events"]
        self.assertTrue(any(row["payload"]["status"] == "Success" for row in calls)); self.assertEqual(ptps, [])
        g02 = self.call("get_collection_history", {"cif": "GOLDEN_G02", "event_types": ["OPERATION", "PTP"]})["data"]["events"]
        self.assertEqual(len({row["source_id"] for row in g02}), len(g02))

    def test_cashflow_missing_zero_and_evidence(self):
        g01 = self.call("get_cashflow_intelligence", {"cif": "GOLDEN_G01"})["data"]
        self.assertFalse(g01["cashflow_available"]); self.assertIsNone(g01["inflow_3d"])
        zero = next(c for c in self.contexts.values() if c["availability"]["cashflow_available"] and c["cashflow"]["inflow_3d"] == 0)
        self.assertEqual(self.call("get_cashflow_intelligence", {"cif": zero["cif"]})["data"]["inflow_3d"], 0)
        g02 = self.call("get_cashflow_intelligence", {"cif": "GOLDEN_G02"})["data"]
        self.assertEqual(g02["inflow_3d"], 40_000_000); self.assertTrue(g02["accepted_rule_ids"])

    def test_policy_golden_and_read_only(self):
        g07 = self.call("get_collection_policy", {"cif": "GOLDEN_G07"})["data"]
        g08 = self.call("get_collection_policy", {"cif": "GOLDEN_G08"})["data"]
        self.assertEqual((g07["base_route"], g07["challenge_override_route"], g07["final_route"]), ("CBS", "CALL", "CALL"))
        self.assertEqual((g08["base_route"], g08["challenge_override_route"], g08["final_route"]), ("CALL", "CBS", "CBS"))
        self.assertFalse(self.call("get_collection_policy", {"cif": "GOLDEN_G07", "new_route": "CBS"})["ok"])
        g07["final_route"] = "FIELD"
        self.assertEqual(self.call("get_collection_policy", {"cif": "GOLDEN_G07"})["data"]["final_route"], "CALL")

    def test_recovery_exact_golden(self):
        for cif, score, baseline, recovery in (("GOLDEN_G01", 28, 1, 917), ("GOLDEN_G02", 58, 1209, 84)):
            tool = self.call("get_recovery_opportunity", {"cif": cif})["data"]; context = self.contexts[cif]
            self.assertEqual(tool["recovery_opportunity_score"], score)
            self.assertEqual((tool["baseline_rank"], tool["recovery_rank"]), (baseline, recovery))
            for key, value in context["recovery_opportunity"].items(): self.assertEqual(tool[key], value)

    def test_cross_tool_g20_and_g04(self):
        row = next(row for row in self.repo.portfolio() if row["cif"] == "GOLDEN_G20")
        self.assertEqual((row["total_outstanding_cif"], row["max_dpd_cif"]), (400_000_000, 12))
        self.assertEqual(self.contexts["GOLDEN_G20"]["debt"]["loan_count"], 3)
        g04 = self.call("get_customer_360", {"cif": "GOLDEN_G04"})["data"]
        self.assertEqual(g04["ptp"]["status"], "BROKEN"); self.assertGreater(g04["cashflow"]["inflow_3d"], 0)

    def test_provenance_forbidden_security_determinism_mutation(self):
        before = tree_hash(self.data)
        for name in TOOL_REGISTRY:
            args = {} if name == "get_portfolio" else {"cif": "GOLDEN_G02"}
            first, second = self.call(name, args), self.call(name, args)
            self.assertEqual(first, second); self.assertTrue(first["meta"]["synthetic_data"])
            self.assertFalse(_keys(first) & FORBIDDEN)
        for unsafe in ({"path": "/etc/passwd"}, {"shell": "id"}, {"url": "https://example.com"}, {"code": "eval('1')"}):
            self.assertFalse(self.call("get_portfolio", unsafe)["ok"])
        self.assertEqual(tree_hash(self.data), before)

    def test_artifact_ab_and_validator(self):
        data_a, data_b = self.root / "fresh-a", self.root / "fresh-b"
        generate_to(data_a); generate_to(data_b)
        report_a, report_b = validate(data_a), validate(data_b)
        self.assertEqual(report_a["status"], "PASS", report_a["errors"])
        self.assertEqual(report_b["status"], "PASS", report_b["errors"])
        a, b = self.root / "artifacts-a", self.root / "artifacts-b"
        write_schema_artifacts(a, "2026-08-28", report_a)
        write_schema_artifacts(b, "2026-08-28", report_b)
        for name in ("tool_schemas.json", "tool_registry_manifest.json", "golden_tool_validation.json"):
            json.loads((a/name).read_text()); json.loads((b/name).read_text())
            self.assertEqual(hashlib.sha256((a/name).read_bytes()).hexdigest(), hashlib.sha256((b/name).read_bytes()).hexdigest())


if __name__ == "__main__": unittest.main()
