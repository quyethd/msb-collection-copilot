---
document_id: 04-call-cbs-routing
title: Phân tuyến CALL / CBS
section: routing
topic: ROUTING
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Phân tuyến CALL / CBS

## Khái niệm

**CALL** và **CBS** là hai tuyến xử lý (route) trong tác nghiệp thu hồi.

- **CALL** — tuyến xử lý qua gọi điện, hướng tới khách hàng cần tương tác trực
  tiếp để thu hồi.
- **CBS** — tuyến nhắc thanh toán và theo dõi cam kết.

Routing là **tuyến xử lý**. Routing không đồng nghĩa action phải thực hiện
ngay.

## Quy tắc routing hiện tại

Điều kiện cơ sở (khi Heatmap = RED, Segment thuộc RED/ORANGE/YELLOW):

- MAX_DPD >= 5 → tuyến **CALL**;
- MAX_DPD < 5 → tuyến **CBS**.

Ngoài điều kiện trên → OTHER/NONE trong prototype.

Challenge-set có thể chuyển tuyến CALL→CBS hoặc CBS→CALL. Trong dữ liệu mô
phỏng, việc chuyển tuyến dùng trường synthetic `challenge_override_route` một
cách tường minh; prototype không giả định đã biết quy tắc challenge thật.

## Routing khác treatment

- Routing trả lời: khách hàng thuộc tuyến xử lý nào.
- Treatment trả lời: hành động cụ thể hôm nay là gì.

Khách thuộc tuyến CALL vẫn có thể nhận hành động "Chờ khách hàng tự thanh toán"
nếu tín hiệu hiện tại đáp ứng điều kiện.

## Thông điệp quan trọng

> Thuộc tuyến CALL không có nghĩa hôm nay cán bộ nhất thiết phải gọi.

Ví dụ tác nghiệp: SYN002846 thuộc tuyến CALL, DPD 11 ngày, tiền vào 7 ngày 48
triệu đồng, dòng tiền ròng 30 ngày 168 triệu đồng, không có cam kết đang mở —
hành động hiện tại là "Chờ khách hàng tự thanh toán", kênh "Chưa cần liên hệ
ngay". Đây là ví dụ minh họa đã được chấp nhận, không phải quy tắc chung.

## Thứ tự quyết định

```text
POLICY → ROUTE → SUPPRESS → PTP/NEXT_ACTION → SCORE → TREATMENT → CHANNEL → WHEN → EXPLAIN
```

High score MUST NOT override hard policy. Routing là quyết định deterministic,
không phải quyết định của AI.