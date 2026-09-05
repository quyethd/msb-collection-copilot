---
document_id: 25-roadmap-and-next-steps
title: Lộ trình và các bước kế tiếp
section: roadmap
topic: ROADMAP
audience: ALL
content_type: overview
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Lộ trình và các bước kế tiếp

## Đã có trong bản demo (IMPLEMENTED / DEMONSTRATED)

- Decision Intelligence: quyết định deterministic theo policy.
- Routing CALL / CBS.
- Recovery Opportunity Scoring (0-100) với thành phần minh bạch.
- Next Best Action (precedence 10 bậc).
- What-if Simulation (clone snapshot + chạy lại cùng engine).
- GreenNode Agent (AgentBase + GLM 5.2): Tool Use, Explain, Investigate,
  Simulate.
- Ứng dụng frontend: Tổng quan, Danh sách ưu tiên, Khách hàng, Tác động dự
  kiến, Giới thiệu hệ thống, Trợ lý.
- Foundation Project Knowledge RAG (TASK-011H): kho kiến thức 26 tài liệu +
  nền tảng RAG với Qwen Flash và triển khai có điều kiện khi có VDB thật.

## Hướng phát triển tiếp theo (FUTURE)

- **Outcome feedback**: kết nối kết quả thanh toán thực sự để học và điều
  chỉnh.
- **Collection pilot + A/B evaluation**: so sánh copilot với baseline trên một
  nhóm pilot.
- **Learning-to-rank**: xếp hạng dựa trên kết quả quan sát thay vì tĩnh.
- **Channel optimization**: tối ưu kênh liên hệ trong ngân sách.
- **Treatment optimization**: tối ưu hành động xử lý.
- **Portfolio monitoring**: theo dõi danh mục liên tục.

## Các bước về nền tảng GreenNode

- **Vector Database (vDB)**: cần product-owner approval để provision OpenSearch
  kNN hoặc PostgreSQL pgvector; sau đó thực hiện ingest thật và "Project
  Knowledge RAG" qua VDB + MaaS.
- **Embedding model**: cần một mô hình embedding trên MaaS hoặc tài nguyên
  embedding được phép; foundation test hiện dùng adapter deterministic local.

## Ghi chú TASK-011H

- TASK-011H không làm thay đổi bất kỳ quyết định nghiệp vụ nào (Decision Core
  giữ nguyên).
- RAG ground-truth chỉ là kiến thức, không phải lệnh hành động.
- Chỉ tích hợp vào giao diện Trợ lý sau khi foundation test PASS và có kế hoạch
  tích hợp riêng.