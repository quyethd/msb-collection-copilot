---
document_id: 01-product-overview
title: Tổng quan sản phẩm — Trợ lý Thu hồi Nợ
section: product_overview
topic: PRODUCT
audience: ALL
content_type: overview
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Tổng quan sản phẩm

## Sản phẩm là gì

MSB Trợ lý Thu hồi Nợ (Collection Decision Copilot) là trợ lý quyết định thu
hồi nợ cho tác nghiệp CALL/CBS. Sản phẩm giúp cán bộ xác định khách hàng nào
nên xử lý trước, vì sao, hành động nào phù hợp và thời điểm nào nên thực hiện.

Thông điệp cốt lõi:

> Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.

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
nghiệp vụ, MaaS cung cấp mô hình ngôn ngữ, và Vector Database dự kiến là lớp
kiến thức dự án. Quyết định thu hồi luôn thuộc về Decision Core deterministic.

## Bản demo

Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.