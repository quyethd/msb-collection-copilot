---
document_id: 23-golden-questions-and-simulated-portfolio
title: Golden questions và danh mục mô phỏng
section: golden_qa
topic: EVALUATION
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Golden questions và danh mục mô phỏng

## Mục đích

Bộ golden questions dùng để đánh giá chất lượng RAG: truy vết được, tái lặp
được, đo được. Mỗi câu hỏi đi kèm metadata về kỳ vọng: topic đúng, tài liệu
đúng, bằng chứng đúng, và các lỗi cấm (forbidden claims).

## Cấu trúc golden questions (TASK-011H)

Kho golden questions cho RAG gồm khoảng 20-25 câu hỏi chia bốn nhóm:

- **Nhóm A — Nghiệp vụ (Business)**: hành vi của hệ thống, quyết định, tuyến
  CALL/CBS, treatment, PTP.
- **Nhóm B — Kiến trúc & Kỹ thuật (Architecture)**: kiến trúc, Decision Core,
  GreenNode, AgentBase, tools.
- **Nhóm C — Định hướng & Tổng quan (Roadmap)**: tổng quan sản phẩm, giá trị,
  lộ trình, nền tảng.
- **Nhóm D — Kỳ vọng đánh giá (Evaluation/Trust)**: bằng chứng, đánh giá, dữ
  liệu mô phỏng, an toàn, ranh giới.

## Danh mục mô phỏng (đã kiểm chứng)

- 3.000 khách hàng mô phỏng, seed 20260828, ngày tham chiếu 2026-08-28.
- Số khách thuộc tuyến CALL: 1.740.
- Số khách thuộc tuyến CALL nhưng hiện chưa cần gọi ngay: 32
  (tuyệt đối **không** diễn giải thành "đã giảm 32 cuộc gọi").
- Số khách có khuyến nghị liên hệ (active contact): 1.933.
- Số khách được đề xuất chờ tự thanh toán: 229.
- Số hồ sơ có hạn chế liên hệ (suppressed): 91.

## Nguyên tắc

- Mỗi câu hỏi chỉ trỏ tới đúng tài liệu/đoạn trong kho kiến thức.
- Câu hỏi về khách hàng cụ thể (SYN..., GOLDEN_...) được phân loại là
  "câu hỏi quyết định / dữ kiện khách hàng" → RAG phải chuyển hướng, không trả
  lời từ kiến thức chung.
- Câu hỏi về simulation một kịch bản cụ thể → SIMULATION_REQUIRED.
- Câu hỏi vượt scope RAG → từ chối bằng mẫu câu không đủ thông tin.