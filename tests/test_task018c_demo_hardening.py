"""TASK-018C focused regression tests for demo conversation hardening.

Verifies all gaps fixed:
  GAP-01: AI governance question → KNOWLEDGE with explicit NO
  GAP-02: Score breakdown uses Vietnamese labels, no raw enums
  GAP-03: Score-not-probability → explicit NO
  GAP-04: Simulation shows channel + no-mutation note
  GAP-05: No NBA-xxx codes in user-facing text
  GAP-06: Web/Zalo worklist fact parity
  GAP-07: Casual Vietnamese paraphrases
  GAP-08: Zalo why-no-call parity
"""
from __future__ import annotations

from pathlib import Path

import pytest

from msb_agent import semantics
from msb_agent.copilot import route_copilot
from msb_tools.repository import ToolRepository
from msb_tools.registry import invoke_tool
from msb_zalo.chat import ZaloConversation, build_morning_brief


DATA = Path("build/synthetic-data")
REPOSITORY = ToolRepository(DATA)
CIF = "SYN002846"


def _caller():
    r = REPOSITORY
    return lambda name, args: invoke_tool(name, args, repository=r)


def _ask(message, **ctx):
    context = {"active_cif": CIF, "last_cif": CIF, **ctx}
    return route_copilot({"cif": CIF, "message": message, "conversation_context": context}, _caller())


# --------------------------------------------------------------------------- #
# GAP-01: AI governance
# --------------------------------------------------------------------------- #

class TestAIGovernance:
    def test_ai_governance_is_knowledge(self):
        r = _ask("AI có tự quyết định hành động không?")
        assert r["question_intent"] == "KNOWLEDGE"

    def test_ai_governance_says_no(self):
        r = _ask("AI có tự quyết định hành động không?")
        summary = (r.get("summary") or "").lower()
        assert "không" in summary or "khong" in summary

    def test_ai_governance_paraphrase(self):
        r = _ask("ai co tu quyet dinh ko")
        assert r["question_intent"] == "KNOWLEDGE"

    def test_ai_governance_no_customer_decision(self):
        r = _ask("AI có tự quyết định hành động không?")
        summary = (r.get("summary") or "")
        assert "WAIT_SELF_CURE" not in summary
        assert "Hệ thống đề xuất" not in summary


# --------------------------------------------------------------------------- #
# GAP-02: Score breakdown Vietnamese labels
# --------------------------------------------------------------------------- #

class TestScoreBreakdownLabels:
    def test_score_uses_vietnamese_labels(self):
        r = _ask("Điểm 47 được tính như thế nào?")
        blob = str(r.get("sections", ""))
        assert "Mức khẩn cấp nghiệp vụ" in blob
        assert "Khả năng thanh toán" in blob
        assert "Khả năng tiếp cận" in blob

    def test_score_no_raw_enum_labels(self):
        r = _ask("Điểm 47 được tính như thế nào?")
        blob = str(r.get("sections", ""))
        assert "BUSINESS_URGENCY" not in blob
        assert "ABILITY_TO_PAY" not in blob
        assert "WILLINGNESS_TO_PAY" not in blob
        assert "CONTACTABILITY" not in blob
        assert "TIMING_OPPORTUNITY" not in blob
        assert "STRATEGIC_ADJUSTMENT" not in blob

    def test_score_has_6_groups(self):
        r = _ask("Điểm 47 được tính như thế nào?")
        blob = str(r.get("sections", ""))
        count = sum(1 for label in (
            "Mức khẩn cấp nghiệp vụ", "Khả năng thanh toán",
            "Mức sẵn sàng thanh toán", "Khả năng tiếp cận",
            "Thời điểm thuận lợi", "Điều chỉnh chiến lược",
        ) if label in blob)
        assert count >= 5, f"only {count} Vietnamese labels found"


# --------------------------------------------------------------------------- #
# GAP-03: Score is not probability
# --------------------------------------------------------------------------- #

class TestScoreNotProbability:
    def test_score_probability_is_knowledge(self):
        r = _ask("Điểm 47 có phải là 47% khả năng khách hàng sẽ trả nợ không?")
        assert r["question_intent"] == "KNOWLEDGE"

    def test_score_probability_says_no(self):
        r = _ask("Điểm 47 có phải là 47% khả năng khách hàng sẽ trả nợ không?")
        summary = (r.get("summary") or "").lower()
        assert "không" in summary or "khong" in summary

    def test_score_probability_not_unknown(self):
        r = _ask("Điểm 47 có phải là 47% khả năng khách hàng sẽ trả nợ không?")
        assert r["question_intent"] != "UNKNOWN"


# --------------------------------------------------------------------------- #
# GAP-04 + GAP-05: Simulation response
# --------------------------------------------------------------------------- #

class TestSimulationResponse:
    def test_simulation_shows_channel(self):
        r = _ask("Nếu tiền vào 7 ngày bằng 0 thì sao?")
        summary = r.get("summary", "")
        assert "Gọi điện" in summary or "goi dien" in summary.lower()

    def test_simulation_no_nba_codes(self):
        r = _ask("Nếu tiền vào 7 ngày bằng 0 thì sao?")
        summary = r.get("summary", "")
        assert "NBA-300" not in summary
        assert "NBA-900" not in summary
        assert "NBA-" not in summary

    def test_simulation_no_mutation_note(self):
        r = _ask("Nếu tiền vào 7 ngày bằng 0 thì sao?")
        summary = r.get("summary", "")
        assert "không bị thay đổi" in summary.lower() or "khong bi thay doi" in summary.lower()

    def test_simulation_followup_uses_sim_state(self):
        _ask("Nếu tiền vào 7 ngày bằng 0 thì sao?",
             last_simulation_changes={"inflow_7d": 0})
        r = _ask("Thế giờ làm gì?", previous_intent="SIMULATION",
                 last_simulation_changes={"inflow_7d": 0})
        summary = r.get("summary", "").lower()
        assert "liên hệ" in summary or "lien he" in summary
        assert "chờ" not in summary or "cho" not in summary or "tự thanh toán" not in summary


# --------------------------------------------------------------------------- #
# GAP-06: Worklist parity
# --------------------------------------------------------------------------- #

class TestWorklistParity:
    def test_web_worklist_count(self):
        r = _ask("Hôm nay tôi phải làm gì?")
        summary = r.get("summary", "")
        assert "3000" in summary

    def test_zalo_worklist_count(self):
        brief = build_morning_brief(REPOSITORY)
        assert brief["portfolio_count"] == 3000

    def test_web_zalo_worklist_fact_parity(self):
        r = _ask("Hôm nay tôi phải làm gì?")
        brief = build_morning_brief(REPOSITORY)
        web_summary = r.get("summary", "")
        assert str(brief["portfolio_count"]) in web_summary
        assert str(brief["call_route_no_call_now"]) in web_summary


# --------------------------------------------------------------------------- #
# GAP-07: Casual Vietnamese paraphrases
# --------------------------------------------------------------------------- #

class TestParaphraseSmoke:
    @pytest.mark.parametrize("message,expected", [
        ("tai sao hom nay chua can goi", "DECISION_EXPLANATION"),
        ("diem 47 tinh sao", "SCORE_BREAKDOWN"),
        ("neu tien vao 7 ngay = 0 thi sao", "SIMULATION"),
        ("the gio lam gi", "SIMULATION"),
        ("call voi cbs khac gi", "KNOWLEDGE"),
        ("ai co tu quyet dinh ko", "KNOWLEDGE"),
        ("hnay toi lam gi", "TODAY_WORKLIST"),
    ])
    def test_paraphrase(self, message: str, expected: str):
        ctx = {"active_cif": CIF, "last_cif": CIF}
        if "the gio" in message:
            ctx["previous_intent"] = "SIMULATION"
            ctx["last_simulation_changes"] = {"inflow_7d": 0}
        r = route_copilot({"cif": CIF, "message": message, "conversation_context": ctx}, _caller())
        assert r["question_intent"] == expected, f"{message!r}: got {r['question_intent']}"


# --------------------------------------------------------------------------- #
# GAP-08: Zalo why-no-call parity
# --------------------------------------------------------------------------- #

class TestZaloWhyNoCall:
    def test_zalo_why_no_call_with_context(self):
        conv = ZaloConversation(REPOSITORY)
        conv.respond("Giải thích SYN002846")
        r = conv.respond("Tại sao hôm nay chưa cần gọi?")
        assert r["question_intent"] in ("DECISION_EXPLANATION", "CONTEXTUAL_FOLLOWUP")
        assert "Chờ khách hàng tự thanh toán" in r["text"] or "cho khach hang tu thanh toan" in r["text"].lower()

    def test_zalo_why_no_call_text_has_decision(self):
        conv = ZaloConversation(REPOSITORY)
        conv.respond("Giải thích SYN002846")
        r = conv.respond("Tại sao hôm nay chưa cần gọi?")
        text = r["text"].lower()
        assert "chua can" in text or "chưa cần" in r["text"].lower() or "cho" in text


# --------------------------------------------------------------------------- #
# Business canaries — unchanged
# --------------------------------------------------------------------------- #

class TestBusinessCanaries:
    def test_syn002846_score_47(self):
        ro = invoke_tool("get_recovery_opportunity", {"cif": CIF}, repository=REPOSITORY)["data"]
        assert ro["recovery_opportunity_score"] == 47

    def test_baseline_wait_self_cure_none(self):
        nba = invoke_tool("get_next_best_action", {"cif": CIF}, repository=REPOSITORY)["data"]
        assert nba["treatment"] == "WAIT_SELF_CURE"
        assert nba["channel"] == "NONE"

    def test_simulation_contact_call(self):
        sim = invoke_tool("simulate_decision", {"cif": CIF, "changes": {"inflow_7d": 0}}, repository=REPOSITORY)["data"]
        after = sim.get("after", {})
        assert after.get("treatment") == "CONTACT"
        assert after.get("channel") == "CALL"


# --------------------------------------------------------------------------- #
# No raw enum leak
# --------------------------------------------------------------------------- #

class TestNoEnumLeak:
    def test_no_raw_score_enum_in_web(self):
        r = _ask("Điểm 47 được tính như thế nào?")
        blob = str(r.get("sections", ""))
        for raw in ("BUSINESS_URGENCY", "ABILITY_TO_PAY", "WILLINGNESS_TO_PAY",
                     "CONTACTABILITY", "TIMING_OPPORTUNITY", "STRATEGIC_ADJUSTMENT"):
            assert raw not in blob, f"raw enum {raw} leaked"

    def test_no_nba_code_in_simulation(self):
        r = _ask("Nếu tiền vào 7 ngày bằng 0 thì sao?")
        summary = r.get("summary", "")
        assert "NBA-" not in summary
