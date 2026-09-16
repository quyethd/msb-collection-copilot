"""TASK-017 real-transcript and state regressions.

These are deliberately deterministic: availability of the optional NLU service
must never change the expected interpretation of an in-scope Zalo request.
"""
from pathlib import Path

from msb_tools.repository import ToolRepository
from msb_tools.registry import invoke_tool
from msb_zalo.chat import ZaloConversation


DATA = Path("build/synthetic-data")
REPOSITORY = ToolRepository(DATA)


def conversation() -> ZaloConversation:
    return ZaloConversation(REPOSITORY)


def test_real_transcript_worklist_paraphrases():
    first = conversation().respond("Nay tao phải làm gì")
    assert first["question_intent"] == "TODAY_PRIORITIES"
    assert "hồ sơ có quyết định" in first["text"]
    for message in (
        "Hôm nay tôi cần thao tác gì", "Tôi cần làm gì", "Có việc gì cần xử lý hôm nay",
        "Hôm nay ưu tiên gì", "Việc hôm nay?", "hnay làm j",
    ):
        assert conversation()._fast_local_intent(message, __import__("msb_zalo.chat", fromlist=["_normalize"])._normalize(message)).intent == "TODAY_PRIORITIES"


def test_real_transcript_priority_and_typo_cif():
    for message in ("Vì sao cần xem SYN001346", "Vì sao tao cần xem sny001346"):
        result = conversation().respond(message)
        assert result["cif"] == "SYN001346"
        assert result["question_intent"] == "EXPLAIN_PRIORITY"
        assert "Điểm cơ hội thu hồi" in result["text"]


def test_active_cif_score_breakdown_never_routes_to_knowledge():
    conv = conversation()
    conv.respond("Giải thích cif SYN001346")
    score = invoke_tool("get_recovery_opportunity", {"cif": "SYN001346"}, repository=REPOSITORY)["data"]["recovery_opportunity_score"]
    for message in ("Điểm được tính như thế nào", "Điểm tính dựa trên gì", "Vì sao điểm chỉ 69"):
        result = conv.respond(message)
        assert result["question_intent"] == "RECOVERY_SCORE_EXPLANATION"
        assert result["cif"] == "SYN001346"
        assert f"{score}/100" in result["text"]


def test_call_cbs_topic_continuity_overrides_active_cif():
    conv = conversation()
    conv.respond("Giải thích SYN001346")
    assert conv.respond("CALL là gì")["question_intent"] == "KNOWLEDGE"
    cbs = conv.respond("CBS thì sao")
    assert cbs["question_intent"] == "KNOWLEDGE"
    assert "CBS là tuyến" in cbs["text"]
    comparison = conv.respond("Khác nhau ở đâu")
    assert comparison["question_intent"] == "KNOWLEDGE"
    assert "CALL và CBS" in comparison["text"]


def test_pending_clarification_resolves_one_word_replies():
    conv = conversation()
    first = conv.respond("Khách không trả nợ thì sao")
    assert first["question_intent"] == "AMBIGUOUS_FOLLOWUP"
    assert "mô phỏng" in first["text"].lower()
    assert conv.respond("mô phỏng")["question_intent"] == "SIMULATION"


def test_simulation_followups_and_cif_isolation():
    conv = conversation()
    conv.respond("Giải thích SYN002846")
    simulated = conv.respond("Nếu tiền vào 7 ngày bằng 0 thì sao")
    assert simulated["question_intent"] == "SIMULATION"
    assert "Liên hệ khách hàng" in simulated["text"]
    assert "mô phỏng" in conv.respond("Thế giờ làm gì")["text"].lower()
    assert "dữ liệu thực" in conv.respond("Quay lại dữ liệu thật")["text"].lower()
    conv.respond("Giải thích SYN000746")
    next_step = conv.respond("Thế giờ làm gì")
    assert next_step["cif"] == "SYN000746"
    assert "mô phỏng" not in next_step["text"].lower()
