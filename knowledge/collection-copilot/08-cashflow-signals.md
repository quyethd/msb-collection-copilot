---
document_id: 08-cashflow-signals
title: Tín hiệu dòng tiền
section: cashflow_signals
topic: CASHFLOW
audience: ALL
content_type: business
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Tín hiệu dòng tiền

## Khái niệm

Tín hiệu dòng tiền được rút ra từ các giao dịch tài chính mô phỏng của khách
hàng, bao gồm:

- **Tiền vào 3/7/30 ngày** (inflow 3d/7d/30d);
- **Dòng tiền ra 30 ngày** (outflow);
- **Dòng tiền ròng 30 ngày** (net cashflow);
- **Tỷ lệ thanh khoản / dư nợ đến hạn** (liquidity-to-due);
- **Dòng tiền lớn gần đây** (recent large inflow);
- **Thu nhập dạng lương** (salary-like income);
- **Độ ổn định thu nhập 90 ngày** (income stability).

## Vai trò của dòng tiền

- Dòng tiền là bằng chứng về **khả năng thanh toán và thời điểm** (ability và
  timing), không tự động là bằng chứng về **thiện chí** (willingness).
- Dòng tiền tốt không tự động chuyển khách ra khỏi tuyến CALL.
- DPD cao + dòng tiền vào tốt có thể làm tăng cơ hội về thời điểm (timing
  opportunity).

## Dòng tiền ảnh hưởng quyết định thế nào

- **Ability to Pay** (25 điểm trong Recovery Opportunity) dùng tiền vào 7 ngày,
  dòng tiền ròng 30 ngày, thu nhập ổn định, tỷ lệ thanh khoản.
- **Timing Opportunity** dùng tiền vào 3 ngày, PTP và next action.
- Trong Next Best Action, "Chờ khách hàng tự thanh toán" yêu cầu tín hiệu dòng
  tiền đáp ứng điều kiện (tiền vào 7 ngày đủ mức, dòng tiền ròng 30 ngày dương).

## Ví dụ minh họa

SYN002846 (mô phỏng): tiền vào 7 ngày = 48 triệu đồng, dòng tiền ròng 30 ngày =
168 triệu đồng → hệ thống đề xuất Chờ khách hàng tự thanh toán. Trong kịch bản
mô phỏng, nếu tiền vào 7 ngày = 0 và dòng tiền ròng = 0, NBA chuyển sang Liên
hệ khách hàng.

## Ranh giới

- Số liệu dòng tiền cụ thể của một khách hàng là dữ liệu khách hàng
  (customer fact), cần truy vấn qua công cụ nghiệp vụ, không phải kiến thức RAG.
- Mô phỏng thay đổi tín hiệu chỉ áp dụng trên bản sao snapshot, không làm thay
  đổi dữ liệu gốc.