---
document_id: 03-problem-and-value-proposition
title: Bài toán và giá trị của giải pháp
section: problem_value
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

# Bài toán và giá trị của giải pháp

## Bài toán ban đầu

Baseline ưu tiên hiện tại dùng **tổng dư nợ theo CIF** và **MAX DPD theo CIF**.
Một CIF có thể có nhiều khoản vay/sản phẩm.

Giả định cần kiểm chứng: dư nợ lớn + DPD cao phản ánh business urgency nhưng
chưa trực tiếp phản ánh cơ hội thu hồi tại thời điểm hiện tại.

## Vì sao dư nợ + DPD chưa đủ

Cán bộ không thiếu dữ liệu. Cán bộ thiếu một quyết định rõ ràng và đáng tin
cậy được tạo ra từ dữ liệu đó.

Bốn điểm khó khăn chính:

1. **Nhiều khách hàng nhưng chưa rõ ai cần xử lý trước.** Danh sách nợ chỉ cho
   biết mức độ quá hạn, không cho biết cơ hội thu hồi tốt nhất tiếp theo. DPD cao
   không đồng nghĩa cơ hội thu hồi tốt nhất; dư nợ cao không đồng nghĩa cần gọi
   ngay.
2. **Một quyết định cần tổng hợp nhiều tín hiệu.** DPD, dư nợ, dòng tiền, cam
   kết thanh toán, lịch sử liên hệ, khả năng liên hệ, next action, tuyến CALL/CBS.
   Chưa có tín hiệu nào đơn lẻ đủ để ra quyết định.
3. **Thuộc tuyến CALL không có nghĩa hôm nay nhất thiết phải gọi.** Tuyến xử lý
   là hướng vận hành. Hành động hôm nay phụ thuộc vào tín hiệu hiện tại.
4. **Cán bộ và quản lý cần hiểu: quyết định vì sao như vậy?** "Tại sao hệ thống
   lại đề xuất hành động này?" phải là câu trả lời được, trên cùng một màn hình.

## Giải pháp

Collection Decision Copilot là AI Agent hỗ trợ Collection Officer/Team Leader
kết hợp policy hiện hữu với dư nợ, DPD, cashflow, PTP, payment behavior và
contact history để đề xuất ưu tiên tác nghiệp.

Luồng quyết định: dữ liệu khách hàng → Hard Policy → Routing → Recovery
Opportunity → Next Best Action → Channel / Timing → GreenNode Agent.

- **Decision Core deterministic** là nguồn quyết định nghiệp vụ.
- **GreenNode Agent** là lớp tương tác, điều phối tool và giải thích.

## Thông điệp demo

- WHO — CIF nào nên xử lý?
- WHY — Vì sao?
- WHAT — Treatment/mục tiêu nào?
- WHEN — Khi nào?

## Ranh giới giá trị

Hệ thống cải thiện **ưu tiên hóa quyết định** dựa trên dữ liệu mô phỏng. Không
khẳng định uplift thu hồi thực tế, xác suất thu hồi sản xuất, hoặc lợi ích tài
chính từ dữ liệu thật.