---
document_id: 01-product-overview
title: Tổng quan sản phẩm — Trợ lý Thu hồi Nợ
section: product_overview
topic: PRODUCT
audience: ALL
content_type: overview
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Tổng quan sản phẩm

## Sản phẩm là gì

MSB Trợ lý Thu hồi Nợ (Collection Decision Copilot) là trợ lý quyết định thu
hồi nợ cho tác nghiệp CALL/CBS. Sản phẩm giúp cán bộ xác định khách hàng nào
nên xử lý trước, vì sao, hành động nào phù hợp và thời điểm nào nên thực hiện.

Thông điệp cốt lõi:

> Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.

## Cấu trúc sản phẩm hiện tại

Sản phẩm gồm ba phần chính:

1. **Trang giới thiệu sản phẩm (landing)** — ở đường dẫn gốc `/`, công khai,
   hiển thị trước khi đăng nhập, giải thích bài toán, giá trị, kiến trúc và độ
   tin cậy. CTA chính: **Đăng nhập hệ thống**.
2. **Trang đăng nhập demo** — ở `/login`, cho phép vào bản demo bằng tài khoản
   demo do team cung cấp (bản demo dùng dữ liệu mô phỏng).
3. **Khu vực ứng dụng (sau đăng nhập)** — gồm Tổng quan, Danh sách ưu tiên,
   Khách hàng, Tác động dự kiến và Trợ lý Thu hồi Nợ trong sidebar.

## Lời hứa giá trị

- Đúng khách hàng
- Đúng hành động
- Đúng thời điểm
- Lý do rõ ràng

## Bốn câu hỏi vận hành

Hệ thống được thiết kế để trả lời bốn câu hỏi vận hành trên cùng một luồng
quyết định:

1. **WHO** — Khách hàng nào nên ưu tiên? → Recovery Opportunity + Ranking.
2. **WHY** — Vì sao khách hàng này được ưu tiên? → Evidence + GreenNode Agent.
3. **WHAT** — Hành động phù hợp là gì? → Next Best Action.
4. **WHEN** — Thực hiện ngay, chờ hay theo dõi? → Cashflow + PTP + callback + suppression + next action.

## Vai trò con người

Agent khuyến nghị; con người quyết định. Trợ lý không tự liên hệ khách hàng,
không tự thay đổi quyết định nghiệp vụ, không tự tạo dữ liệu.

## Nền tảng

Sản phẩm được xây dựng trên nền GreenNode AI: AgentBase điều phối công cụ
nghiệp vụ, MaaS cung cấp mô hình ngôn ngữ (GLM 5.2, Qwen Flash), và Vector
Database (vDB OpenSearch) lưu và truy xuất vector kho tri thức dự án. Kho tri
thức hiện tại chạy thật trên GreenNode vDB (TASK-011H live proof), phiên bản
kiến thức **TASK-011H-V2**. Embedding dùng mô hình đa ngôn ngữ local
(MiniLM-L12), không chạy trên MaaS. Quyết định thu hồi luôn thuộc về Decision
Core deterministic; RAG chỉ truy xuất kiến thức, chưa tích hợp vào Trợ lý
production (COPILOT_INTEGRATION=NO).

## Bản demo

Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.