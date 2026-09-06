---
document_id: 05-recovery-opportunity
title: Recovery Opportunity — Điểm cơ hội thu hồi
section: recovery_opportunity
topic: RECOVERY_SCORE
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Recovery Opportunity — Điểm cơ hội thu hồi

## Khái niệm

Recovery Opportunity là **điểm ưu tiên tương đối** phản ánh cơ hội thu hồi tốt
nhất tại thời điểm hiện tại, chứ không phải xác suất khách hàng chắc chắn
thanh toán.

## Các thành phần điểm

Điểm tổng nằm trong khoảng 0–100, gồm sáu thành phần:

| Thành phần                 | Điểm tối đa |
|----------------------------|-------------|
| Business Urgency           | 20          |
| Ability to Pay             | 25          |
| Willingness to Pay         | 20          |
| Contactability             | 15          |
| Timing Opportunity         | 15          |
| Strategic Adjustment       | 5           |

Weights/thresholds nằm trong cấu hình và có thể chỉnh được.

## Điểm khác với xếp hạng cũ

- Baseline cũ: ưu tiên theo tổng dư nợ CIF + MAX DPD.
- Recovery Opportunity: kết hợp thêm khả năng trả, thiện chí, khả năng liên hệ
  và cơ hội thời điểm để tìm "cơ hội thu hồi tốt nhất tiếp theo".

Ranking mới từ Recovery Opportunity dùng cho ưu tiên tác nghiệp. Sự khác biệt
giữa baseline và copilot ranking **không** được coi là mức cải thiện thu hồi
đã chứng minh.

## Nguyên tắc dữ liệu

- Thiếu bằng chứng được đánh dấu `MISSING` và đóng góp 0, không phải là hành vi
  tiêu cực.
- Strategic Adjustment mặc định là 0 trong V1 khi chưa cấu hình.
- Điểm số luôn nằm trong 0–100 (ràng buộc kiểm chứng).

## Ranh giới

Recovery Opportunity không phải xác suất trả nợ thực tế, không phải chính sách
MSB chính thức. Là quy tắc prototype có cấu hình minh bạch.