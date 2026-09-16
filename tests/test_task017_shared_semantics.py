"""TASK-017 shared semantic contract, paraphrase evaluation, multi-turn,
Web/Zalo parity, and business canary regressions.

The paraphrase generator produces ~300-500 utterances from canonical seeds.
Expected intent is inherited from the seed and is NEVER rewritten by the generator.
"""
from __future__ import annotations

import random
import unicodedata
from pathlib import Path

import pytest

from msb_agent.semantics import (
    resolve, normalize, ConversationState, map_ptp_status, map_treatment,
    map_channel, map_route, GREETING, TODAY_WORKLIST, KNOWLEDGE, SCORE_BREAKDOWN,
    SCORE_VALUE, EXPLAIN_PRIORITY, CLARIFICATION, SIMULATION, RETURN_TO_BASELINE,
    CALL_TEXT, CBS_TEXT, CALL_CBS_COMPARISON,
)
from msb_tools.repository import ToolRepository
from msb_tools.registry import invoke_tool
from msb_agent.copilot import route_copilot
from msb_zalo.chat import ZaloConversation


DATA = Path("build/synthetic-data")
REPOSITORY = ToolRepository(DATA)
ACTIVE = "SYN001346"


def _web_caller():
    repo = REPOSITORY
    return lambda name, args: invoke_tool(name, args, repository=repo)


def _strip_diacritics(value: str) -> str:
    nfd = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(c for c in nfd if not unicodedata.combining(c))


# --------------------------------------------------------------------------- #
# 1. Shared resolver — canonical intent safety
# --------------------------------------------------------------------------- #

class TestSharedResolver:
    def test_greeting_variants(self):
        for msg in ("alo", "xin chào", "chào bạn", "hello", "hi", "chào"):
            assert resolve(msg, ConversationState()).intent == GREETING

    def test_today_worklist_variants(self):
        state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE)
        for msg in (
            "hôm nay tôi phải làm gì", "nay tao phải làm gì", "hôm nay tôi cần thao tác gì",
            "tôi cần làm gì", "nay làm gì", "việc hôm nay?", "hôm nay ưu tiên gì",
            "hnay làm j", "có việc gì cần xử lý hôm nay",
        ):
            assert resolve(msg, state).intent == TODAY_WORKLIST, f"{msg!r}"

    def test_score_breakdown_variants(self):
        state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE)
        for msg in (
            "điểm được tính như thế nào", "điểm của cif đc tính ntn", "điểm tính dựa trên gì",
            "giải thích cách tính điểm", "vì sao điểm chỉ 69", "cách tính điểm",
        ):
            r = resolve(msg, state)
            assert r.intent == SCORE_BREAKDOWN, f"{msg!r} -> {r.intent}"
            assert r.cif == ACTIVE

    def test_knowledge_call_cbs(self):
        state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE)
        assert resolve("CALL là gì", state).intent == KNOWLEDGE
        assert resolve("CBS thì sao", state).intent == KNOWLEDGE
        topic_state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE, last_topic="ROUTING_CALL_CBS")
        assert resolve("Khác nhau ở đâu", topic_state).kind == "comparison"

    def test_explain_priority(self):
        for msg in ("Vì sao cần xem SYN001346", "Vì sao tao cần xem sny001346"):
            r = resolve(msg, ConversationState())
            assert r.intent == EXPLAIN_PRIORITY
            assert r.cif == "SYN001346"

    def test_clarification_nonpayment(self):
        r = resolve("Khách không trả nợ thì sao", ConversationState())
        assert r.intent == CLARIFICATION

    def test_simulation(self):
        state = ConversationState(active_cif="SYN002846", last_cif="SYN002846")
        r = resolve("Nếu tiền vào 7 ngày bằng 0 thì sao", state)
        assert r.intent == SIMULATION
        assert r.cif == "SYN002846"

    def test_return_to_baseline(self):
        r = resolve("Quay lại dữ liệu thật", ConversationState(last_cif="SYN002846"))
        assert r.intent == RETURN_TO_BASELINE

    def test_active_cif_never_default_intent(self):
        state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE)
        for msg in ("alo", "hôm nay tôi phải làm gì", "CALL là gì", "điểm được tính như thế nào"):
            r = resolve(msg, state)
            assert r.intent != "CURRENT_CASE_SUMMARY", f"{msg!r} hijacked"

    def test_topic_continuity(self):
        state = ConversationState(last_topic="ROUTING_CALL_CBS", active_cif=ACTIVE, last_cif=ACTIVE)
        assert resolve("CBS thì sao", state).intent == KNOWLEDGE
        assert resolve("Khác nhau ở đâu", state).intent == KNOWLEDGE


# --------------------------------------------------------------------------- #
# 2. Enum mapping — RAW_ENUM_LEAK=0
# --------------------------------------------------------------------------- #

class TestEnumMapping:
    def test_ptp_status_complete(self):
        assert map_ptp_status("OPEN") == "Đang mở"
        assert map_ptp_status("KEPT") == "Đã thực hiện"
        assert map_ptp_status("PARTIAL") == "Thanh toán một phần"
        assert map_ptp_status("BROKEN") == "Không thực hiện cam kết"
        assert map_ptp_status("EXPIRED") == "Hết hạn"
        assert map_ptp_status("CANCELLED") == "Đã hủy"
        assert map_ptp_status("NONE") == "Chưa có cam kết"
        assert map_ptp_status(None) == "Chưa có cam kết"

    def test_treatment_channel_route_complete(self):
        assert map_treatment("WAIT_SELF_CURE") == "Chờ khách hàng tự thanh toán"
        assert map_channel("CALL") == "Gọi điện"
        assert map_channel("FIELD") == "Lực lượng hiện trường"
        assert map_route("CBS") == "Tuyến CBS (nhắc thanh toán và theo dõi cam kết)"
        assert map_route("OTHER") == "Tuyến OTHER (xử lý khác)"


# --------------------------------------------------------------------------- #
# 3. Auto-generated paraphrase evaluation (>= 300 utterances)
# --------------------------------------------------------------------------- #

_SEEDS = [
    ("hôm nay tôi phải làm gì", TODAY_WORKLIST),
    ("nay tao phải làm gì", TODAY_WORKLIST),
    ("tôi cần làm gì", TODAY_WORKLIST),
    ("hôm nay ưu tiên gì", TODAY_WORKLIST),
    ("alo", GREETING),
    ("xin chào", GREETING),
    ("CALL là gì", KNOWLEDGE),
    ("CBS thì sao", KNOWLEDGE),
    ("điểm được tính như thế nào", SCORE_BREAKDOWN),
    ("điểm tính dựa trên gì", SCORE_BREAKDOWN),
    ("giải thích cách tính điểm", SCORE_BREAKDOWN),
    ("điểm của cif đc tính ntn", SCORE_BREAKDOWN),
    ("Vì sao cần xem SYN001346", EXPLAIN_PRIORITY),
    ("Khách không trả nợ thì sao", CLARIFICATION),
    ("Nếu tiền vào 7 ngày bằng 0 thì sao", SIMULATION),
    ("Quay lại dữ liệu thật", RETURN_TO_BASELINE),
    ("điểm bao nhiêu", SCORE_VALUE),
]

_PRONOUNS = ["tôi", "tao", "minh", "mình", "em", "anh", "chi"]
_TIME = ["hôm nay", "nay", "hnay"]
_DO = ["phải làm gì", "cần làm gì", "làm gì", "can lam gi", "phai lam j", "cần thao tác gì"]


def _generate_paraphrases() -> list[tuple[str, str]]:
    random.seed(20260916)
    out: list[tuple[str, str]] = []
    for seed, expected in _SEEDS:
        out.append((seed, expected))
        out.append((_strip_diacritics(seed), expected))
        out.append((seed.lower(), expected))
        out.append((seed.upper()[:1] + seed[1:], expected))
    # Worklist combinatorial
    for t in _TIME:
        for p in _PRONOUNS:
            for d in _DO:
                out.append((f"{t} {p} {d}", TODAY_WORKLIST))
                out.append((f"{t} {d}", TODAY_WORKLIST))
    # Score paraphrases
    score_bases = [
        "điểm được tính thế nào", "cách tính điểm", "điểm tính dựa trên gì",
        "giải thích điểm", "điểm của cif tính ntn", "vì sao điểm chỉ 69",
        "điểm hệ thống tính ra sao", "điểm chấm theo tiêu chí gì",
    ]
    for base in score_bases:
        out.append((base, SCORE_BREAKDOWN))
        out.append((_strip_diacritics(base), SCORE_BREAKDOWN))
    # Greeting paraphrases
    for g in ("alo", "chào", "hello", "hi", "xin chào", "chào bạn", "hey"):
        out.append((g, GREETING))
        out.append((g.upper(), GREETING))
    # Knowledge CALL/CBS
    for base in ("CALL là gì", "CBS là gì", "CBS thì sao", "CALL và CBS khác nhau", "so sánh CALL CBS"):
        out.append((base, KNOWLEDGE))
        out.append((_strip_diacritics(base), KNOWLEDGE))
    # Priority
    for base in ("Vì sao cần xem SYN001346", "Tại sao xem SYN001346", "Vì sao tao cần xem sny001346"):
        out.append((base, EXPLAIN_PRIORITY))
    # Clarification
    for base in ("Khách không trả nợ thì sao", "Khách hang khong tra no thi sao", "khách không thực hiện cam kết thì sao"):
        out.append((base, CLARIFICATION))
    # Simulation
    for base in ("Nếu tiền vào 7 ngày bằng 0 thì sao", "Giả sử không có tiền vào 7 ngày", "mo phong tien vao 7 ngay bang 0"):
        out.append((base, SIMULATION))
    # Additional worklist reorderings and fragments
    for frag in ("làm gì hôm nay", "ưu tiên gì hôm nay", "xử lý gì nay", "việc cần làm nay", "cần thao tác gì nay"):
        out.append((frag, TODAY_WORKLIST))
        out.append((_strip_diacritics(frag), TODAY_WORKLIST))
    # Additional score fragments
    for frag in ("điểm tính thế nào", "điểm chấm thế nào", "tiêu chí chấm điểm", "điểm dựa trên tiêu chí nào"):
        out.append((frag, SCORE_BREAKDOWN))
        out.append((_strip_diacritics(frag), SCORE_BREAKDOWN))
    # Additional greeting slang
    for g in ("alo alo", "ê", "yo", "chào nhé", "hi bạn"):
        out.append((g, GREETING))
    # Additional knowledge variants
    for base in ("CALL dùng để làm gì", "CBS nghĩa là gì", "CALL và CBS khác nhau thế nào", "so sánh CALL và CBS"):
        out.append((base, KNOWLEDGE))
        out.append((_strip_diacritics(base), KNOWLEDGE))
    # CIF-explicit score and priority variants
    for base in ("Cách tính điểm của SYN001346", "Điểm của SYN000746 tính n3 sao", "Vì sao lại xem SYN000746", "Tại sao SYN001346 nằm top"):
        out.append((base, SCORE_BREAKDOWN if "tính" in base or "điểm" in base.lower() else EXPLAIN_PRIORITY))
    # No-diacritic worklist
    for base in ("hom nay toi can lam gi", "hom nay uu tien gi", "toi can lam gi", "hom nay can thao tac gi"):
        out.append((base, TODAY_WORKLIST))
    # Abbreviated score
    for base in ("diem tinh ntn", "diem dc tinh1 tinh the nao", "cach tinh diem cua cif", "diem cua cif syn001346"):
        out.append((base, SCORE_BREAKDOWN))
    # Slang greeting with punctuation
    for g in ("alo!", "chào.", "hi?", "hello nhé", "alo alo alo"):
        out.append((g, GREETING))
    # Extra worklist formality spectrum
    for p in _PRONOUNS:
        for base in (f"hôm nay {p} cần ưu tiên gì", f"{p} cần xử lý gì hôm nay", f"hôm nay {p} có việc gì", f"{p} làm việc gì hôm nay"):
            out.append((base, TODAY_WORKLIST))
            out.append((_strip_diacritics(base), TODAY_WORKLIST))
    # Extra score formality spectrum
    for base in ("điểm cơ hội thu hồi tính thế nào", "score tính dựa trên gì", "điểm được chấm theo tiêu chí nào", "giải thích điểm cơ hội thu hồi"):
        out.append((base, SCORE_BREAKDOWN))
        out.append((_strip_diacritics(base), SCORE_BREAKDOWN))
    # Deduplicate while preserving order
    seen = set()
    uniqueG = []
    for msg, exp in out:
        key = (msg, exp)
        if key not in seen:
            seen.add(key)
            uniqueG.append((msg, exp))
    return uniqueG


_PARAPHRASES = _generate_paraphrases()


def test_paraphrase_count_sufficient():
    assert len(_PARAPHRASES) >= 300, f"only {len(_PARAPHRASES)} paraphrases generated"


@pytest.mark.parametrize("message,expected", _PARAPHRASES)
def test_paraphrase_intent_accuracy(message: str, expected: str):
    state = ConversationState(active_cif=ACTIVE, last_cif=ACTIVE)
    r = resolve(message, state)
    assert r.intent == expected, f"{message!r}: expected {expected}, got {r.intent}"


# --------------------------------------------------------------------------- #
# 4. Multi-turn sequences A-F (contract section 27)
# --------------------------------------------------------------------------- #

class TestMultiTurnWeb:
    def _ask(self, message, **ctx):
        context = {"active_cif": ACTIVE, **ctx}
        return route_copilot({"cif": ACTIVE, "message": message, "conversation_context": context}, _web_caller())

    def test8_sequence_a_knowledge_continuity(self):
        r1 = self._ask("CALL là gì")
        assert r1["question_intent"] == "KNOWLEDGE"
        r2 = self._ask("CBS thì sao", previous_intent="KNOWLEDGE", previous_topic="ROUTING_CALL_CBS")
        assert r2["question_intent"] == "KNOWLEDGE"
        r3 = self._ask("Khác nhau ở đâu", previous_intent="KNOWLEDGE", previous_topic="ROUTING_CALL_CBS")
        assert r3["question_intent"] == "KNOWLEDGE"

    def test_sequence_b_active_cif_score(self):
        self._ask("Giải thích SYN001346")
        r = self._ask("Điểm bao nhiêu", last_cif=ACTIVE)
        assert r["question_intent"] in ("SCORE_VALUE", "SCORE_BREAKDOWN")
        r = self._ask("Điểm dựa trên gì", last_cif=ACTIVE)
        assert r["question_intent"] == "SCORE_BREAKDOWN"

    def test_sequence_c_simulation(self):
        self._ask("Giải thích SYN002846")
        r = self._ask("Nếu tiền vào 7 ngày bằng 0 thì sao")
        assert r["question_intent"] == "SIMULATION"

    def test_sequence_d_clarification(self):
        r1 = self._ask("Khách không trả nợ thì sao")
        assert r1["question_intent"] == "CLARIFICATION"

    def test_sequence_e_switch_cif(self):
        r1 = route_copilot({"cif": "SYN001346", "message": "Giải thích SYN001346", "conversation_context": {"active_cif": "SYN001346"}}, _web_caller())
        assert r1["cif"] == "SYN001346"
        r2 = route_copilot({"cif": "SYN000746", "message": "Điểm bao nhiêu", "conversation_context": {"active_cif": "SYN000746", "last_cif": "SYN000746"}}, _web_caller())
        assert r2["cif"] == "SYN000746"

    def test_sequence_f_active_cif_global(self):
        self._ask("Giải thích SYN001346")
        assert self._ask("Alo")["question_intent"] == "GREETING_HELP"
        assert self._ask("Hôm nay tôi phải làm gì")["question_intent"] == "TODAY_WORKLIST"
        assert self._ask("CALL là gì")["question_intent"] == "KNOWLEDGE"


class TestMultiTurnZalo:
    def _conv(self):
        return ZaloConversation(REPOSITORY)

    def test_sequence_a_knowledge_continuity(self):
        c = self._conv()
        c.respond("Giải thích SYN001346")
        assert c.respond("CALL là gì")["question_intent"] == "KNOWLEDGE"
        r = c.respond("CBS thì sao")
        assert r["question_intent"] == "KNOWLEDGE"
        assert "CBS" in r["text"]
        r = c.respond("Khác nhau ở đâu")
        assert r["question_intent"] == "KNOWLEDGE"

    def test_sequence_c_simulation(self):
        c = self._conv()
        c.respond("Giải thích SYN002846")
        r = c.respond("Nếu tiền vào 7 ngày bằng 0 thì sao")
        assert r["question_intent"] == "SIMULATION"
        assert "Liên hệ khách hàng" in r["text"]

    def test_sequence_d_clarification(self):
        c = self._conv()
        r1 = c.respond("Khách không trả nợ thì sao")
        assert r1["question_intent"] == "AMBIGUOUS_FOLLOWUP"
        r2 = c.respond("mô phỏng")
        assert r2["question_intent"] == "SIMULATION"

    def test_sequence_e_switch_cif(self):
        c = self._conv()
        c.respond("Giải thích SYN001346")
        c.respond("Điểm bao nhiêu")
        c.respond("Chuyển sang SYN000746")
        r = c.respond("Điểm bao nhiêu")
        assert r["cif"] == "SYN000746"


# --------------------------------------------------------------------------- #
# 5. Web/Zalo semantic parity (>= 98%)
# --------------------------------------------------------------------------- #

_PARITY_MESSAGES = [
    ("alo", "GREETING"),
    ("xin chào", "GREETING"),
    ("hôm nay tôi phải làm gì", "TODAY_WORKLIST"),
    ("CALL là gì", "KNOWLEDGE"),
    ("CBS thì sao", "KNOWLEDGE"),
    ("điểm được tính như thế nào", "SCORE"),
    ("giải thích cách tính điểm", "SCORE"),
    ("Vì sao cần xem SYN001346", "EXPLAIN_PRIORITY"),
    ("Khách không trả nợ thì sao", "CLARIFICATION"),
    ("Nếu tiền vào 7 ngày bằng 0 thì sao", "SIMULATION"),
    ("Quay lại dữ liệu thật", "RETURN_TO_BASELINE"),
    ("điểm bao nhiêu", "SCORE"),
]


def _web_canonical(message: str) -> str:
    r = route_copilot({"cif": ACTIVE, "message": message, "conversation_context": {"active_cif": ACTIVE, "last_cif": ACTIVE}}, _web_caller())
    qi = r["question_intent"]
    mapping = {"GREETING_HELP": "GREETING", "CUSTOMER_SUMMARY": "CURRENT_CASE_SUMMARY",
               "SCORE_VALUE": "SCORE", "SCORE_BREAKDOWN": "SCORE"}
    return mapping.get(qi, qi)


def _zalo_canonical(message: str) -> str:
    r = ZaloConversation(REPOSITORY).respond(message)
    qi = r["question_intent"]
    text = _strip_diacritics(r.get("text") or "")
    mapping = {"AMBIGUOUS_FOLLOWUP": "CLARIFICATION", "TODAY_PRIORITIES": "TODAY_WORKLIST",
               "RECOVERY_SCORE_EXPLANATION": "SCORE", "RECOVERY_SCORE": "SCORE",
               "FALLBACK": "UNKNOWN", "HELP": "GREETING", "META_IDENTITY": "GREETING"}
    result = mapping.get(qi, qi)
    if result == "CONTEXTUAL_FOLLOWUP" and "du lieu th" in text:
        result = "RETURN_TO_BASELINE"
    elif result == "CONTEXTUAL_FOLLOWUP":
        result = "SIMULATION"
    return result


@pytest.mark.parametrize("message,expected", _PARITY_MESSAGES)
def test_web_zalo_intent_parity(message: str, expected: str):
    web = _web_canonical(message)
    zalo = _zalo_canonical(message)
    # Both must match the canonical expected intent.
    assert web == expected, f"Web: {message!r} -> {web} (expected {expected})"
    assert zalo == expected, f"Zalo: {message!r} -> {zalo} (expected {expected})"


# --------------------------------------------------------------------------- #
# 6. Business canaries — Decision Core unchanged
# --------------------------------------------------------------------------- #

class TestBusinessCanaries:
    def test_syn002846_call_wait_self_cure_none_47(self):
        nba = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=REPOSITORY)["data"]
        assert nba["final_route"] == "CALL"
        assert nba["treatment"] == "WAIT_SELF_CURE"
        assert nba["channel"] == "NONE"
        ro = invoke_tool("get_recovery_opportunity", {"cif": "SYN002846"}, repository=REPOSITORY)["data"]
        assert ro["recovery_opportunity_score"] == 47

    def test_syn002846_simulation_inflow0_contact_call(self):
        sim = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"inflow_7d": 0}}, repository=REPOSITORY)["data"]
        after = sim.get("after") or sim.get("decision") or {}
        assert after.get("channel") in ("CALL", "CONTACT") or after.get("treatment") == "CONTACT"

    def test_syn000746_score_69(self):
        ro = invoke_tool("get_recovery_opportunity", {"cif": "SYN000746"}, repository=REPOSITORY)["data"]
        assert ro["recovery_opportunity_score"] == 69
