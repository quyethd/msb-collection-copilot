---
document_id: 22-synthetic-data
title: Dữ liệu mô phỏng (Synthetic Data)
section: synthetic_data
topic: DATA
audience: ALL
content_type: business
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Dữ liệu mô phỏng (Synthetic Data)

## Sự thật quan trọng

> Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.

Không có thông tin nhận dạng cá nhân thật, không có hồ sơ tín dụng thật, không
có giao dịch thật trong bản demo.

## Cấu hình mô phỏng

- **Số khách hàng**: 3.000 (3.000 CIF mô phỏng).
- **Seed**: 20260828 (seed cố định, tái lập được).
- **Ngày tham chiếu**: 2026-08-28.
- **Cấu trúc danh mục**: tổng dư nợ theo CIF, nhiều khoản vay trên một CIF, tần
  suất trả nợ, nhóm sản phẩm, phân bố loan rate và giá trị tài sản đảm bảo.

## Bộ khách hàng vàng (golden)

Bộ golden gồm 20 khách hàng mẫu G01-G20, trong đó 5 khách HERO (G01-G05) dùng
cho trình diễn. Các khách hàng vàng được thiết kế để demo các tình huống đặc
biệt:

- G01 (HERO): thuộc tuyến CALL nhưng hành động hiện tại là Chờ khách hàng tự
  thanh toán.
- G02: thuộc tuyến CALL với cam kết thanh toán được theo dõi.
- Các khác: tình huống CBS, khách không liên hệ được, PTP mở/broken, v.v.

## Ứng dụng

- Số liệu trên các trang Tổng quan, Danh sách ưu tiên, Tác động dự kiến đều đến
  từ dữ liệu mô phỏng.
- Các con số như 3.000 khách hàng, 1.740 thuộc tuyến CALL, 32 khách thuộc tuyến
  CALL nhưng chưa cần gọi ngay là số liệu của danh mục mô phỏng.
- Không được phát biểu rằng "đã giảm 32 cuộc gọi" hay "thu hồi tăng X%" — chỉ
  nêu: 32 khách thuộc tuyến gọi điện nhưng hiện chưa cần gọi ngay (trong bản
  demo mô phỏng).

## Ranh giới

Các kết quả từ dữ liệu mô phỏng không phải là kết quả hoạt động thu hồi thực
tế và không được trình bày như vậy.