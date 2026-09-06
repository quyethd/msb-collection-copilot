---
document_id: 25-roadmap-and-next-steps
title: Lộ trình và các bước kế tiếp
section: roadmap
topic: ROADMAP
audience: ALL
content_type: overview
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
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
- Sản phẩm web theo TASK-011I: landing công khai `/`, đăng nhập demo `/login`,
  và khu vực ứng dụng gồm Tổng quan, Danh sách ưu tiên, Khách hàng, Tác động
  dự kiến và Trợ lý trong sidebar.
- Project Knowledge RAG (TASK-011H): kho kiến thức 26 tài liệu, phiên bản kiến
  thức TASK-011H-V2.
- Live RAG trên GreenNode: GreenNode vDB OpenSearch đã provision, ingest/truy xuất
  live + Qwen Flash trả lời có nguồn (TASK-011H live proof PASS,
  INFERENCE_ANCHOR=LIVE_GREENNODE_VDB).

## Hướng phát triển tiếp theo (FUTURE)

- **Outcome feedback**: kết nối kết quả thanh toán thực sự để học và điều chỉnh.
- **Collection pilot + A/B evaluation**: so sánh copilot với baseline trên một
  nhóm pilot.
- **Learning-to-rank**: xếp hạng dựa trên kết quả quan sát thay vì tĩnh.
- **Channel optimization**: tối ưu kênh liên hệ trong ngân sách.
- **Treatment optimization**: tối ưu hành động xử lý.
- **Portfolio monitoring**: theo dõi danh mục liên tục.
- **Tích hợp RAG vào Trợ lý production** (COPILOT_INTEGRATION): kết nối lớp
  kiến thức RAG (TASK-011H-A.1, đã live) vào giao diện Trợ lý — chưa thực hiện
  (COPILOT_INTEGRATION=NO).

## Các bước về nền tảng GreenNode

- **Vector Database (vDB)**: đã provision OpenSearch kNN và kết nối thật — ingest
  + truy xuất live PASS. Bản V2 hiện tại lưu ở index `msb-collection-knowledge-v2`,
  bản V1 được giữ ở index `msb-collection-knowledge-v1`.
- **Embedding model**: MaaS chưa có mô hình embedding được cấp phép; hiện dùng
  mô hình đa ngôn ngữ local (MiniLM-L12, 384 chiều). Có thể chuyển sang
  GreenNode khi có model embedding trên MaaS.

## Ghi chú TASK-011H

- TASK-011H không làm thay đổi bất kỳ quyết định nghiệp vụ nào (Decision Core
  giữ nguyên).
- RAG ground-truth chỉ là kiến thức, không phải lệnh hành động.
- Chỉ tích hợp vào giao diện Trợ lý sau khi foundation test PASS và có kế hoạch
  tích hợp riêng.