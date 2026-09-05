---
document_id: 17-system-architecture
title: Kiến trúc hệ thống
section: architecture
topic: ARCHITECTURE
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Kiến trúc hệ thống

## Tổng quan luồng

Người dùng thao tác qua giao diện MSB và API ứng dụng. Quyết định nghiệp vụ
được xử lý bởi **Decision Core deterministic** từ dữ liệu mô phỏng. Khi người
dùng hỏi Trợ lý, GreenNode Agent hiểu câu hỏi tự nhiên, chọn đúng công cụ
nghiệp vụ, lấy quyết định từ Decision Core rồi giải thích dựa trên bằng chứng.

## Các lớp

1. **FRONTEND** — Tổng quan, Danh sách ưu tiên, Khách hàng, Tác động dự kiến,
   Giới thiệu hệ thống, Trợ lý.
2. **API / DEMO LAYER** — Customer 360, Portfolio, Timeline, Events, Impact.
3. **DETERMINISTIC DECISION CORE** — Policy, Recovery Score, NBA, Simulation.
4. **GRENNODE AGENT** — Tool Use, Explain, Investigate, Simulate, Summary.
5. **DATA / CONTEXT** — Customer, Loan, Cashflow, PTP, Call history (dữ liệu mô
   phỏng).

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