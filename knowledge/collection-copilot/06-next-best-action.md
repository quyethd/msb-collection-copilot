---
document_id: 06-next-best-action
title: Next Best Action — Hành động phù hợp tiếp theo
section: next_best_action
topic: NBA
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Next Best Action — Hành động phù hợp tiếp theo

## Khái niệm

Next Best Action (NBA) là tầng quyết định chọn **hành động phù hợp** cho một
khách hàng theo mức ưu tiên và tín hiệu hiện tại. Kết quả NBA bao gồm:

- **treatment** — hành động (ví dụ: Chờ, Nhắc thanh toán, Liên hệ, Theo dõi cam
  kết, Gọi lại, Xác minh liên hệ, Chuyển mức xử lý);
- **channel** — kênh thực hiện;
- **objective** — mục tiêu;
- **when** — thời điểm;
- **reason** — lý do chính.

## Thứ tự ưu tiên (precedence)

```text
1. Hard suppression
2. Callback / source next action
3. Verify contact
4. Partial PTP
5. Broken PTP
6. Open PTP
7. Kept PTP
8. Self-cure
9. RTP escalation
10. Default by final route
```

First-match-wins: quy tắc khớp trước có quyền ưu tiên cao hơn. Quy tắc thấp
hơn không được phủ quyết quy tắc cao hơn. High score không được phủ quyết hard
policy.

## Các nhóm hành động (giao diện nghiệp vụ)

- Chờ
- Chờ khách hàng tự thanh toán
- Nhắc thanh toán
- Liên hệ
- Theo dõi cam kết
- Khôi phục cam kết
- Thanh toán một phần
- Gọi lại
- Xác minh liên hệ
- Chuyển mức xử lý

Giao diện hiển thị hành động thân thiện với nghiệp vụ, không hiển thị mã nội
bộ.

## Ví dụ

- SYN002846 (mô phỏng): tuyến CALL nhưng NBA hiện tại là **Chờ khách hàng tự
  thanh toán**, kênh **Chưa cần liên hệ ngay**.
- Khi cán bộ thay đổi tín hiệu trong mô phỏng (tiền vào 7 ngày = 0, dòng tiền
  ròng = 0), NBA thay đổi sang **Liên hệ khách hàng**.

## Ranh giới quyết định

- NBA do Decision Core deterministic tạo ra.
- AI (Agent) đọc kết quả NBA qua business tool và giải thích, không tự thay
  đổi NBA.
- Không xác định NBA của một khách hàng cụ thể trên dữ liệu khách hàng thật
  trong bản demo.