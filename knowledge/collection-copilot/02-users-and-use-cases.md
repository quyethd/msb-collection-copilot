---
document_id: 02-users-and-use-cases
title: Người dùng và tình huống sử dụng
section: users_and_use_cases
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

# Người dùng và tình huống sử dụng

## Người dùng trực tiếp

### Cán bộ tác nghiệp thu hồi

- **Tác nghiệp CALL** — người gọi điện cho khách hàng.
- **Tác nghiệp CBS** — người nhắc thanh toán và theo dõi cam kết.

Giá trị nhận được:

- biết khách hàng nào nên ưu tiên;
- biết trường hợp nào thuộc tuyến CALL nhưng chưa cần gọi ngay;
- xem hành động phù hợp;
- xem lý do trên cùng một màn hình;
- giảm việc tự tổng hợp nhiều nguồn dữ liệu.

### Team Leader / Collection Manager

Quản lý và phân bổ tác nghiệp.

- nhìn tổng quan danh mục;
- phân bổ hành động;
- xem danh sách ưu tiên;
- phát hiện trường hợp cần chú ý;
- theo dõi tác động vận hành.

### Kiến trúc / Công nghệ

Chuyên gia xem xét tính bền vững.

- deterministic decision;
- traceable rules;
- AI cannot override NBA;
- grounded tool use;
- testable architecture;
- clear module boundaries;
- guardrails;
- auditability.

### Ban giám khảo Hackathon

Đánh giá bài toán, giải pháp, giá trị và độ tin cậy của hệ thống thông qua
trang giới thiệu sản phẩm công khai (landing) và các bằng chứng kiểm chứng.

## Truy cập sản phẩm

1. Mở trang giới thiệu sản phẩm (landing) tại `/` — công khai, chưa cần đăng nhập.
2. Chọn **Đăng nhập hệ thống** để tới trang đăng nhập demo `/login`.
3. Đăng nhập bằng tài khoản demo do team cung cấp để vào khu vực ứng dụng `/app`.
4. Trong khu vực ứng dụng, dùng sidebar để chuyển giữa Tổng quan, Danh sách ưu
   tiên, Khách hàng, Tác động dự kiến và mở Trợ lý.

## Tình huống sử dụng điển hình

Một ngày tác nghiệp với Trợ lý Thu hồi Nợ:

- 08:00 — Mở Tổng quan: xem danh mục, tuyến xử lý và các điểm cần chú ý.
- 08:05 — Mở Danh sách ưu tiên: xác định khách hàng nên xử lý trước.
- 08:10 — Mở hồ sơ khách hàng: xem dư nợ, DPD, dòng tiền, PTP, lịch sử liên hệ và hành động đề xuất.
- 08:12 — Hỏi Trợ lý: "Tại sao hôm nay chưa nên gọi khách hàng này?"
- 08:15 — Thực hiện hành động: liên hệ / nhắc / theo dõi PTP / chờ tự thanh toán theo quyết định hiện tại.

## Ranh giới

Sản phẩm là trợ lý quyết định, không phải hệ thống thay thế quyết định của
cán bộ và không tự động liên hệ khách hàng.