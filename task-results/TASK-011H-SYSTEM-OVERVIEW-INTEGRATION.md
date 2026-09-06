# TASK-011H — SYSTEM OVERVIEW INTEGRATION NOTES

## Scope of this note
TASK-011H did NOT modify the System Overview page or the frontend. These notes describe exactly how a
future task would surface the Project Knowledge RAG as a truth-traceable capability consistent with the
existing System Overview landing content and the TASK-011H safety statements.

## Guardrails
- Do NOT claim the copilot is live: `GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL`, `LIVE_QWEN_RAG=NOT_RUN`,
  `PROJECT_KNOWLEDGE_RAG_LIVE=NOT_PROVEN`, `COPILOT_INTEGRATION=NO`.
- Do NOT claim real customer-data grounding: all reasoning today runs on the curated corpus
  (`knowledge/collection-copilot`) and the synthetic portfolio, anchor `LOCAL_MOCKED_VDB`.

## What could be shown later (once gates pass)
- Architecture block: "Người dùng hỏi Trợ lý → Knowledge RAG (corpus + vector DB + Qwen Flash) → trả lời
  có trích dẫn nguồn" alongside the existing decision pipeline; the deterministic Decision Core still owns
  per-CIF decisions.
- Trust statements that match proven evidence:
  - Trả lời dựa trên kho kiến thức dự án, có **trích dẫn tài liệu nguồn**.
  - Câu hỏi quyết định theo CIF, số liệu thực, hoặc mô phỏng → **không trả lời từ RAG**, yêu cầu dữ liệu/engine.
  - Câu hỏi nhạy cảm bảo mật bị chặn.
  - Không có thông tin đủ → trả lời **"chưa tìm thấy đủ thông tin"** thay vì bịa.
  - Không phát biểu "đã giảm 32 cuộc gọi" hay uplift/ROI.
- Where to wire labels that mirror the existing evaluation/trust evidence:
  `knowledge_version=TASK-011H-V1`, `Recall@3=0.96`, `GROUNDING=0.96`, `CITATION=1.0`, `BOUNDARY=1.0`
  (LOCAL_MOCKED_VDB anchor only; never print live-equivalents).

## Concrete integration points (for the future task)
- Tool surface: a `get_project_knowledge_answer` (or `onUserQuery`) tool registered in `msb_tools` that
  calls `KnowledgeRagService.answer`; Agent explains from returned sources and cites document ids.
- Boundary-first routing: the classifier in `src/msb_knowledge_rag/classifier.py` must run before retrieval
  in the copilot path so per-CIF questions still flow to the Decision Core tools/engine.
- Override/guardrail semantics: unchanged — RAG output never overrides an accepted business decision.
- No UI change inside the isolated branch; any System Overview text change stays a separate approved task.

## Deployment note
No deployment in TASK-011H. `DOCROOT` untouched; `index.html`/assets unchanged.