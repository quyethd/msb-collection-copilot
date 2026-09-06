---
document_id: 17-system-architecture
title: Kiến trúc hệ thống
section: architecture
topic: ARCHITECTURE
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Kiến trúc hệ thống

## Tổng quan luồng

Người dùng thao tác qua giao diện MSB và API ứng dụng. Quyết định nghiệp vụ
được xử lý bởi **Decision Core deterministic** từ dữ liệu mô phỏng. Khi người
dùng hỏi Trợ lý, GreenNode Agent hiểu câu hỏi tự nhiên, chọn đúng công cụ
nghiệp vụ, lấy quyết định từ Decision Core rồi giải thích dựa trên bằng chứng.

## Các lớp

1. **FRONTEND** — Ứng dụng (sau đăng nhập): Tổng quan, Danh sách ưu tiên, Khách
   hàng, Tác động dự kiến, Trợ lý trong sidebar. Trang công khai: landing `/`,
   đăng nhập demo `/login`.
2. **API / DEMO LAYER** — Customer 360, Portfolio, Timeline, Events, Impact,
   demo auth `/demo/auth/login`.
3. **DETERMINISTIC DECISION CORE** — Policy, Recovery Score, NBA, Simulation.
4. **GRENNODE AGENT** — Tool Use, Explain, Investigate, Simulate, Summary.
5. **DATA / CONTEXT** — Customer, Loan, Cashflow, PTP, Call history (dữ liệu mô
   phỏng). Vector kho kiến thức dự án lưu tại **GreenNode vDB OpenSearch**.

## Kiến thức RAG trên GreenNode vDB

- Kho kiến thức dự án (phiên bản **TASK-011H-V2**) được lưu dưới dạng vector
  trong index vDB OpenSearch của GreenNode (kNN, cosine similarity).
- Truy xuất: câu hỏi được nhúng về vector để tìm các đoạn kiến thức liên quan
  (chunk); Qwen Flash tổng hợp câu trả lời có nguồn từ các chunk truy xuất được.
- Embedding chạy **local** (mô hình đa ngôn ngữ MiniLM-L12, 384 chiều); MaaS
  hiện không có mô hình embedding để cấp phép.
- Đã kiểm chứng live: ingest và truy xuất trên GreenNode vDB thật
  (TASK-011H live proof). RAG chưa tích hợp vào giao diện Trợ lý production
  (COPILOT_INTEGRATION=NO).

## Decision Core

- **msb_policy**: hard policy, routing, ràng buộc nghiệp vụ.
- **msb_recovery**: Recovery Opportunity Score.
- **msb_nba**: Next Best Action và thứ tự ưu tiên.
- **msb_simulation**: chạy tình huống deterministic, không làm thay đổi context
  gốc.
- **msb_impact**: tác động vận hành và ước tính minh bạch theo giả định.

## GreenNode Agent layer

- **msb_agent**: Agent runtime — điều phối tool, giải thích, điều tra, mô phỏng.
- **msb_agent_eval**: đánh giá độ tin cậy của Trợ lý (tool use đúng, so khớp
  quyết định, unknown CIF an toàn, override guardrail, không lộ private
  reasoning).

## Business tools (registry)

- get_portfolio
- get_customer_360
- get_collection_history
- get_cashflow_intelligence
- get_collection_policy
- get_recovery_opportunity
- get_next_best_action
- simulate_decision

## Nguyên tắc quyền lực

- Deterministic Decision Core = **source of truth** cho routing, score,
  treatment, channel, timing.
- GreenNode Agent = lớp tương tác và điều phối.
- GreenNode không phải yếu tố trang trí: Agent dùng để tương tác tự nhiên, chọn
  công cụ, giải thích có căn cứ, điều tra và mô phỏng — còn quyết định thu hồi
  vẫn do engine deterministic nắm giữ.
- RAG không tự quyết định khách hàng thuộc tuyến CALL hay CBS: tuyến xử lý do
  Decision Core xác định từ policy; RAG chỉ truy vấn kiến thức dự án.