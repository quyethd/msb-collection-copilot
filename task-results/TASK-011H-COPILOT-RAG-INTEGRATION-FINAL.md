# TASK-011H-B: Copilot RAG Integration (Project Knowledge V2) — FINAL

Ngày: 2026-09-06 · Nhánh: master (sau merge `task-011h-greennode-rag`) · Không deploy.

## Tóm tắt
Trợ lý Thu hồi Nợ (`/demo/copilot`) của ứng dụng chính đã tích hợp **Luồng Kiến thức Hệ thống (Project Knowledge RAG V2)** đã được chấp nhận ở TASK-011H-A.1: nhúng đa ngôn ngữ cục bộ → GreenNode Vector Database (`msb-collection-knowledge-v2`, 129 đoạn) → Qwen Flash (tổng hợp đáp án có nguồn). Ranh giới khách hàng/quyết định/mô phỏng/bảo mật giữ nguyên trên Bộ máy quyết định. Trang public hiển thị GreenNode (AgentBase, MaaS, GLM 5.2, Qwen Flash, vDB, nhúng cục bộ) và tách bạch hai luồng.

## Cập nhật mã nguồn chính
- `src/msb_agent/copilot.py`:
  - Thêm intent `KNOWLEDGE`; quy trình phân loại: rỗng→OUT_OF_SCOPE → chào→GREETING_HELP → **bí mật→OUT_OF_SCOPE(0.99)** → dấu hiệu kiến thức→**KNOWLEDGE(0.97)** → SIMULATION→PTP→CASHFLOW→ROUTE→DECISION→CUSTOMER (thứ tự giữ 12 ví dụ regression).
  - `_knowledge_service()`: singleton lười (`KnowledgeRagConfig` + `MaasRagAnswerer` + `KnowledgeRagService`), chỉ tải khi có câu hỏi kiến thức.
  - `_knowledge_response()`: ánh xạ `RagAnswer` → contract copilot (`mode=KNOWLEDGE`, `path=RAG_QWEN`, `sections` gồm "Câu trả lời" và "Nguồn tham khảo" dạng `i. <tiêu đề> — <mục>`, `metadata` chứa các latency, `knowledge_version=TASK-011H-V2`, `qwen_fast_model`). Lỗi dịch vụ → fall mềm về `LOW_CONFIDENCE_REFUSAL`.
- `tests/test_task011h_b.py` (mới): phân loại (12 câu kiến thức, 7 câu khách hàng/ranh giới, 4 câu bí mật bị chặn), contract response, nguồn có thể đọc, ranh giới giữ nguyên, secret bị chặn trước khi gọi RAG, khách hàng giữ nguyên Decision Core.
- Môi trường (chỉ local, không commit giá trị): `.env` → `GRENNODE_VDB_INDEX=msb-collection-knowledge-v2`, `RAG_EMBEDDING_PROVIDER=local-multilingual`; `.env.example` bổ sung tài liệu vDB/RAG/Qwen.
- Frontend:
  - `assistant-question-catalog.ts`: + nhóm `Kiến thức sản phẩm` (4 câu) → **14 câu chung**; `commonAssistantQuestions` giữ 4 câu đầu.
  - `main.tsx` (Copilot): trạng thái theo giai đoạn trung thực ("Đang xác định nội dung câu hỏi..." → "Đang tìm trong kho kiến thức..." → "GreenNode AI đang tổng hợp câu trả lời..."), trạng thái cuối riêng cho RAG ("Đã tìm thấy nguồn liên quan."), highlight "Nguồn tham khảo", "Xem thêm 10 câu hỏi", footer RAG chân thực.
  - Landing: `content.ts` + `SystemOverviewPage.tsx` + `system-overview.css` — nền tảng GreenNode mở rộng (7 thẻ: AgentBase, MaaS, GLM 5.2, Qwen Flash, Vector Database, nhúng đa ngôn ngữ cục bộ, Decision Core), mục mới "Trợ Lý Hiểu Cả Quyết Định Và Kiến Thức Hệ Thống", kiến trúc tách **LUỒNG KHÁCH HÀNG / QUYẾT ĐỊNH** và **LUỒNG KIẾN THỨC HỆ THỐNG**, trạng thái kiểm chứng live-proof chân thực, trust badges +RAG, FAQ +2, câu hỏi mẫu 14.

## Kiểm chứng
- Backend pytest (PYTHONPATH=src, python hệ thống):
  - `test_task011h_a` + `test_task011h_knowledge` + `test_task011h_b` + `test_task011g` + `test_task011i`: **83 passed** (~100s; fastembed load).
  - Engines (synthetic/policy/recovery/nba/tools/context/evaluation/impact): **114 passed** (tools ~167s, context ~227s — chậm nhưng đậu).
  - Task files: `test_task007b` 48, `test_task008` 47, `test_task009b` 21, `test_task011` 3, `test_task011d` 6 — đậu.
  - `test_task008b`: 64 passed + **3 pre-existing failures** (auth-assertions cũ: `/demo/timeline/`, `/demo/reset/`, `/demo/events` browser-safe từ TASK-011I landing public — `tool_server.py` không thay đổi trong task này; xem git `698a4be`).
- Frontend: `npm test` **50 passed**; `npm run build` **PASS**.
- QA render thực tế (Playwright, headless):
  - `DRAWER_QA=PASS` (3 viewports: 4 gợi ý → mở rộng **14** câu, **5** nhóm, "Xem thêm 10 câu hỏi", z-index backdrop/drawer, không tràn).
  - `RAG_QA=PASS` (4 viewports 1366x768 / 1440x900 / 1920x1080 / 390x844 — landing hiển thị đủ GreenNode/vDB/Qwen/TASK-011H-V2/two-paths; live hỏi "CALL và CBS khác nhau thế nào?" → drawer hiện **"Nguồn tham khảo"**, footer RAG, không còn status cũ).
  - `LAYOUT_QA=PASS`, `PRIORITY=PASS` (điều chỉnh login cho landing public sau TASK-011I).
- `git -c core.whitespace=cr-at-eol diff --check` **OK** (`.env.example` là tệp CRLF sẵn có của repo).

## Ranh giới / an toàn
- Khách hàng/quyết định/mô phỏng/ưu tiên/bối cảnh → Decision Core (công cụ đã chấp nhận). Kiến thức hệ thống không quyết định nghiệp vụ.
- Bí mật (API key, mật khẩu, `.env`, credentials, reasoning_content...) bị chặn ở ranh giới trước khi gọi RAG. Không tiết lộ endpoint/vector nội bộ.
- Nguồn trả lời kiến thức chỉ xuất hiện khi truy xuất được đoạn đủ đáng tin; nếu không đủ, Trợ lý nói rõ. Không khẳng định nâng tỷ lệ thu hồi, không gán nhãn "PASS" cạnh AgentBase, không lộ runtime spike.
- Ngôn ngữ: tiếng Việt — Tiếng Anh thuật ngữ ("RAG", "vDB", "MaaS", "Recovery Opportunity", "Decision Core"...) đều có giải thích (`UNEXPLAINED_ENGLISH_TERM=0`; `VI_FIRST_ANSWER=PASS`).

## Blob fields
```
KNOWLEDGE_VERSION=TASK-011H-V2
COPILOT_PROJECT_KNOWLEDGE=PASS
COPILOT_CUSTOMER_BOUNDARY=PASS
COPILOT_SIMULATION_BOUNDARY=PASS
COPILOT_SECURITY_BOUNDARY=PASS
LIVE_GREENNODE_VDB=PASS
LIVE_QWEN_RAG=PASS
COPILOT_CITATIONS=PASS
VI_FIRST_ANSWER=PASS
UNEXPLAINED_ENGLISH_TERM=0
LANDING_GREENNODE_VISIBILITY=PASS
AGENTBASE_VISIBLE=PASS
QWEN_VISIBLE=PASS
VDB_VISIBLE=PASS
TESTS=FE 50 passed · BE 386 passed (3 pre-existing stale auth asserts in test_task008b documented)
BUILD=PASS
BUSINESS_SEMANTICS_DRIFT=0
DEPLOY=NO
```