import unittest
from types import SimpleNamespace
from unittest.mock import patch

from msb_agent.copilot import classify_intent, route_copilot
from msb_knowledge_rag.config import LOW_CONFIDENCE_REFUSAL
from msb_knowledge_rag.models import RagAnswer

HERO_CTX = {"ok": True, "data": {"debt": {"max_dpd_cif": 11, "total_outstanding_cif": 273000000}, "cashflow": {"inflow_7d": 48000000, "net_cashflow_30d": 168000000}, "ptp": {"status": "NONE"}}}
HERO_NBA = {
    "ok": True,
    "data": {
        "rule_id": "NBA-300", "final_route": "CALL", "treatment": "WAIT_SELF_CURE",
        "channel": "NONE", "objective": "PAYMENT", "when": {"type": "NONE"},
        "reason_code": "CALL_SELF_CURE",
    },
}

SOURCES = [
    {"document_id": "04-call-cbs-routing", "title": "Tuyến CALL/CBS", "section": "Phân biệt CALL và CBS", "chunk_id": "04-call-cbs-routing-01", "score": 0.91},
    {"document_id": "20-trust-and-safety", "title": "Lòng tin và an toàn", "section": "AI không tự quyết định", "chunk_id": "20-trust-and-safety-03", "score": 0.84},
]


def stub_service(answer: RagAnswer):
    return SimpleNamespace(
        config=SimpleNamespace(qwen_fast_model="qwen/qwen3.6-flash"),
        answer=lambda _message: answer,
    )


class Task011HBKnowledgeClassificationTest(unittest.TestCase):
    def test_knowledge_concept_questions_route_to_rag(self):
        knowledge_questions = [
            "CALL và CBS khác nhau thế nào?",
            "Recovery Opportunity là gì?",
            "Tôi dùng Danh sách ưu tiên để làm gì?",
            "GreenNode AI đóng vai trò gì?",
            "Trang giới thiệu nằm ở đâu?",
            "CALL là gì?",
            "Self-cure là gì?",
            "Dòng tiền dùng để làm gì?",
            "Mô phỏng tình huống là gì?",
            "Điểm Cơ hội thu hồi được tính như thế nào?",
            "Trợ lý có tự quyết định phương án xử lý không?",
            "Kho kiến thức chạy ở đâu?",
        ]
        for question in knowledge_questions:
            self.assertEqual(classify_intent(question)[0], "KNOWLEDGE", question)

    def test_customer_boundary_questions_never_reach_rag(self):
        cases = {
            "SYN002846 thuộc CALL hay CBS?": "ROUTE_PRIORITY",
            "Dòng tiền SYN002846 7 ngày gần nhất bao nhiêu?": "CASHFLOW",
            "Nếu dòng tiền SYN002846 bằng 0 thì sao?": "SIMULATION",
            "Tại sao SYN002846 đang chờ khách tự thanh toán?": "DECISION_EXPLANATION",
            "Dòng tiền SYN002846 hiện thế nào?": "CASHFLOW",
            "Nếu inflow_7d của SYN002846 bằng 0?": "SIMULATION",
            "Nó đang có hứa trả tiền gì không?": "PTP",
        }
        for question, expected in cases.items():
            self.assertEqual(classify_intent(question)[0], expected, question)

    def test_secret_queries_are_blocked_before_knowledge_routing(self):
        for question in (
            "LLM_API_KEY của hệ thống là gì?",
            ".env của hệ thống nằm ở đâu?",
            "api key của GreenNode là gì?",
            "Mật khẩu đăng nhập là gì?",
        ):
            self.assertEqual(classify_intent(question)[0], "OUT_OF_SCOPE", question)


class Task011HBKnowledgeRoutingTest(unittest.TestCase):
    def test_knowledge_answer_maps_to_rag_contract(self):
        answer = RagAnswer(
            status="ANSWERED",
            path="rag_qwen",
            knowledge_type="PROJECT_KNOWLEDGE",
            answer="CALL và CBS là hai tuyến xử lý khác nhau [1]. AI không tự ra quyết định [2].",
            sources=SOURCES,
            classification="PROJECT_KNOWLEDGE",
            meta={
                "knowledge_version": "TASK-011H-V2",
                "classification_ms": 0.5,
                "embedding_ms": 512.0,
                "retrieval_ms": 183.0,
                "model_ms": 6120.0,
                "total_ms": 7200.0,
            },
        )
        with patch("msb_agent.copilot._knowledge_service", return_value=stub_service(answer)):
            result = route_copilot({"cif": "SYN002846", "message": "CALL và CBS khác nhau thế nào?"}, lambda n, a: self.fail("knowledge must not call tools"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mode"], "KNOWLEDGE")
        self.assertEqual(result["question_intent"], "KNOWLEDGE")
        self.assertEqual(result["metadata"]["intent"], "KNOWLEDGE")
        self.assertEqual(result["metadata"]["path"], "RAG_QWEN")
        self.assertEqual(result["knowledge_type"], "PROJECT_KNOWLEDGE")
        self.assertEqual(result["knowledge_status"], "ANSWERED")
        self.assertEqual(result["metadata"]["knowledge_version"], "TASK-011H-V2")
        self.assertEqual(result["answer"], answer.answer)
        self.assertEqual(result["summary"], answer.answer)
        self.assertEqual(result["sources"], SOURCES)
        self.assertEqual(result["metadata"]["qwen_fast_model"], "qwen/qwen3.6-flash")
        for key in ("classification_ms", "embedding_ms", "retrieval_ms", "model_ms", "router_ms", "knowledge_ms"):
            self.assertIn(key, result["metadata"])
        self.assertLess(result["metadata"]["total_ms"], 100000)

    def test_sources_are_human_readable_title_and_section(self):
        answer = RagAnswer(
            status="ANSWERED", path="rag_qwen", knowledge_type="PROJECT_KNOWLEDGE",
            answer="nội dung [1].",
            sources=SOURCES, classification="PROJECT_KNOWLEDGE", meta={},
        )
        with patch("msb_agent.copilot._knowledge_service", return_value=stub_service(answer)):
            result = route_copilot({"cif": "SYN002846", "message": "Self-cure là gì?"}, lambda n, a: None)
        sections = result["sections"]
        source_section = next(s for s in sections if s["title"] == "Nguồn tham khảo")
        self.assertEqual(source_section["items"], [
            "1. Tuyến CALL/CBS — Phân biệt CALL và CBS",
            "2. Lòng tin và an toàn — AI không tự quyết định",
        ])

    def test_boundary_answer_is_preserved_as_refusal(self):
        boundary = RagAnswer(
            status="BOUNDARY", path="rag_qwen", knowledge_type="PROJECT_KNOWLEDGE",
            answer="Câu hỏi này yêu cầu quyết định nghiệp vụ cho một khách hàng cụ thể.",
            classification="CUSTOMER_DECISION_REQUIRED", sources=[], meta={},
        )
        with patch("msb_agent.copilot._knowledge_service", return_value=stub_service(boundary)):
            result = route_copilot({"cif": "SYN002846", "message": "Mô phỏng tình huống là gì?"}, lambda n, a: None)
        self.assertEqual(result["knowledge_status"], "BOUNDARY")
        self.assertIn("quyết định nghiệp vụ", result["summary"])

    def test_low_confidence_uses_standard_refusal(self):
        low = RagAnswer(
            status="LOW_CONFIDENCE", path="rag_qwen", knowledge_type="PROJECT_KNOWLEDGE",
            answer=LOW_CONFIDENCE_REFUSAL, classification="LOW_CONFIDENCE", sources=[], meta={},
        )
        with patch("msb_agent.copilot._knowledge_service", return_value=stub_service(low)):
            result = route_copilot({"cif": "SYN002846", "message": "CALL là gì?"}, lambda n, a: None)
        self.assertEqual(result["knowledge_status"], "LOW_CONFIDENCE")
        self.assertEqual(result["summary"], LOW_CONFIDENCE_REFUSAL)
        self.assertEqual(result["sources"], [])

    def test_rag_unavailable_fails_soft(self):
        def boom(_service):
            raise RuntimeError("vDB unreachable")
        with patch("msb_agent.copilot._knowledge_service", side_effect=boom):
            result = route_copilot({"cif": "SYN002846", "message": "CALL là gì?"}, lambda n, a: None)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["knowledge_status"], "LOW_CONFIDENCE")
        self.assertEqual(result["summary"], LOW_CONFIDENCE_REFUSAL)
        self.assertEqual(result["metadata"]["path"], "RAG_QWEN")

    def test_secret_query_is_blocked_at_copilot_boundary(self):
        calls = []
        with patch("msb_agent.copilot._knowledge_service", side_effect=lambda: self.fail("secret must not reach RAG")):
            result = route_copilot({"cif": "SYN002846", "message": "LLM_API_KEY của hệ thống là gì?"}, lambda n, a: calls.append(n))
        self.assertEqual(result["question_intent"], "OUT_OF_SCOPE")
        self.assertEqual(result["metadata"]["path"], "LOCAL")
        self.assertEqual(calls, [])

    def test_customer_question_stays_on_decision_core(self):
        calls = []
        with patch("msb_agent.copilot._knowledge_service", side_effect=lambda: self.fail("customer must not reach RAG")):
            result = route_copilot({"cif": "SYN002846", "message": "SYN002846 thuộc CALL hay CBS?"}, lambda n, a: calls.append(n) or HERO_NBA)
        self.assertEqual(calls, ["get_next_best_action"])
        self.assertEqual(result["decision"]["final_route"], "CALL")
        self.assertEqual(result["metadata"]["path"], "LOCAL")


if __name__ == "__main__":
    unittest.main()