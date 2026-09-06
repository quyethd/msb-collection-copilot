---
document_id: 09-self-cure
title: Self-cure — Chờ khách hàng tự thanh toán
section: self_cure
topic: SELF_CURE
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Self-cure — Chờ khách hàng tự thanh toán

## Khái niệm

Self-cure là tình huống hệ thống đề xuất **chờ khách hàng tự thanh toán** thay
vì liên hệ ngay, dựa trên tín hiệu hiện tại. Self-cure không làm đổi tuyến xử
lý: một khách thuộc tuyến CALL vẫn thuộc CALL, chỉ là hành động hôm nay là chờ.

## Điều kiện SELF-CURE (prototype, có thể cấu hình)

Khách hàng chỉ đủ điều kiện chờ tự thanh toán khi tất cả điều kiện sau đúng:

- tuyến là CALL hoặc CBS;
- DPD không vượt ngưỡng (ngưỡng hiện tại: DPD <= 14);
- không có cam kết thanh toán đang mở (PTP state = NONE);
- kết quả nghiệp vụ gần nhất không phải RTP hoặc NIN;
- dữ liệu dòng tiền sẵn có;
- dòng tiền ròng 30 ngày > 0;
- tiền vào 7 ngày đạt mức tối thiểu cấu hình (hiện tại >= 15 triệu đồng);
- không có hạn chế xử lý (hard suppression);
- không có ngày hành động tiếp theo từ nguồn (source next action date).

Kết quả:

- CALL + đủ điều kiện → "Chờ khách hàng tự thanh toán" (WAIT_SELF_CURE), kênh
  chưa cần liên hệ.
- CBS + đủ điều kiện → "Chờ theo dõi", kênh chưa cần liên hệ.

## Nguyên tắc an toàn

- DPD cao + dòng tiền tốt **không** được self-cure chỉ vì cashflow tốt.
- Self-cure không được phủ quyết hard suppression hoặc hard policy.
- Self-cure là quyết định deterministic của Decision Core, không phải do AI.

## Ý nghĩa nghiệp vụ

> Thuộc tuyến CALL không có nghĩa hôm nay cán bộ nhất thiết phải gọi.

Trường hợp này cho phép cán bộ tập trung nguồn lực vào khách hàng thực sự cần
tương tác, đồng thời theo dõi diễn biến dòng tiền và cam kết của khách đang
chờ.