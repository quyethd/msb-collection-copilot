---
document_id: 07-ptp
title: PTP — Cam kết thanh toán
section: ptp
topic: PTP
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# PTP — Cam kết thanh toán

## Khái niệm

PTP (Promise to Pay) là cam kết thanh toán của khách hàng. PTP là tín hiệu quan
trọng về thiện chí và thời điểm của khách hàng.

## Các trạng thái PTP

| Trạng thái | Ý nghĩa |
|-----------|---------|
| OPEN | Đang có cam kết thanh toán, chưa tới hạn và chưa thanh toán đủ. |
| KEPT | Đã thanh toán đủ theo cam kết (actual_paid >= promised). |
| PARTIAL | Thanh toán một phần (0 < actual_paid < promised). |
| BROKEN | Cam kết không thực hiện (paid = 0 sau ngày hứa + thời gian gia hạn). |
| NONE | Không có cam kết đang mở. |

## Các khái niệm liên quan

- **Fulfillment ratio**: mức hoàn thành cam kết, tính bằng min(actual/promised, 1)
  nếu promised > 0.
- **PTP ability**: đánh giá của nhân viên về khả năng thực hiện cam kết
  (CERTAIN / HIGH / MEDIUM / LOW / VERY_LOW). Đây chỉ là tín hiệu hỗ trợ về
  willingness, không phải quyết định cứng.
- **Payment after contact**: khoảng thời gian từ khi tương tác đến khi khách
  thanh toán — tín hiệu hỗ trợ đánh giá thiện chí.

## PTP ảnh hưởng quyết định thế nào

Trạng thái PTP là đầu vào chính cho Next Best Action:

- OPEN → Theo dõi cam kết thanh toán.
- PARTIAL → Theo dõi khoản thanh toán một phần.
- BROKEN + có dòng tiền gần đây → Xử lý cam kết không thực hiện.
- BROKEN (khác) → Liên hệ.
- KEPT → Chờ theo dõi.

## Ranh giới

- Trạng thái kỹ thuật của cuộc gọi không được đồng nhất với kết quả nghiệp vụ
  (PTP/payment).
- PTP không tự động = willingness cao; tín hiệu dòng tiền không tự động =
  willingness.
- Hệ thống không tự tạo PTP cho khách hàng; AI không được tự tạo cam kết thanh
  toán.