---
document_id: 14-impact-page-guide
title: Hướng dẫn trang Tác động dự kiến
section: user_guide
topic: IMPACT
audience: MANAGER
content_type: product_guide
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Hướng dẫn trang Tác động dự kiến

## Mục đích

Trang Tác động dự kiến giúp quản lý hiểu **giá trị vận hành tiềm năng** của
giải pháp theo cách minh bạch: phân biệt rõ số đo được từ bản demo, giả định có
thể chỉnh sửa, và ước tính dẫn xuất.

## Bốn phần chính

1. **Đo được ngay** — các con số từ output deterministic của bản demo: tổng
   khách hàng (3.000), tỷ lệ có quyết định, số khách thuộc tuyến CALL, số khách
   thuộc tuyến CALL nhưng hiện chưa cần gọi ngay, số khuyến nghị liên hệ.
2. **Baseline vs Copilot** — so sánh thứ tự xếp hạng cũ (dư nợ + DPD) và thứ tự
   từ Recovery Opportunity/NBA.
3. **Giả định đầu vào có thể chỉnh sửa** — số ngày làm việc, số khách xem mỗi
   ngày, phút xem mỗi hồ sơ, phút mỗi cuộc gọi, chi phí nhân sự mỗi giờ.
4. **Giá trị vận hành ước tính** — giờ tiết kiệm, số cuộc gọi tiềm năng tránh
   mỗi ngày, ước tính chi phí vận hành và công thức minh bạch.

## Nguyên tắc không phóng đại

- "32 khách thuộc tuyến CALL nhưng hiện chưa cần gọi ngay" là số lượng hồ sơ
  trong bản demo mô phỏng, **không** phải "đã giảm 32 cuộc gọi".
- Các giá trị kinh tế (AEV estimate) là **ước tính theo giả định đầu vào**, không
  phải số liệu vận hành thực tế.
- Không có recovery uplift, không có ROI được khẳng định như kết quả thực.

## Trang này dùng để làm gì

Trả lời câu hỏi: "Hệ thống có thể giúp giảm công sức rà soát và tập trung nguồn
lực thế nào, theo giả định nào, minh bạch ra sao?"