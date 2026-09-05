---
document_id: 13-customer-page-guide
title: Hướng dẫn trang Khách hàng
section: user_guide
topic: USER_GUIDE
audience: COLLECTION_OFFICER
content_type: product_guide
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Hướng dẫn trang Khách hàng

## Mục đích

Trang Khách hàng cung cấp **ngữ cảnh đầy đủ của một khách hàng** để cán bộ
hiểu vì sao hệ thống đưa ra quyết định hiện tại và thử kịch bản khác.

## Nội dung chính

- **Thông tin nợ**: dư nợ, DPD, khoản vay, tổng dư nợ theo CIF.
- **Tuyến xử lý và trạng thái**: CALL/CBS, trạng thái hạn chế xử lý.
- **Dòng tiền**: tiền vào 3/7/30 ngày, dòng tiền ròng 30 ngày.
- **PTP**: trạng thái cam kết thanh toán, ngày cam kết.
- **Lịch sử liên hệ / tác nghiệp**: cuộc gọi, lần liên hệ thành công, thời điểm
  liên hệ tốt.
- **Điểm cơ hội thu hồi và phân rã thành phần**.
- **Hành động đề xuất (NBA)** kèm lý do.
- **Mô phỏng tình huống**: thay đổi tín hiệu và xem quyết định trước/sau.
- **Trợ lý**: hỏi về quyết định của khách hàng bằng ngôn ngữ tự nhiên.
- **Dòng thời gian sự kiện** và thông tin kỹ thuật.

## Trợ lý trên trang Khách hàng

Trợ lý hiện tại hỗ trợ trả lời câu hỏi **về quyết định** của khách hàng đang
xem, dựa trên quyết định đã được xác định và dữ liệu khách hàng hiện có, ví dụ:

- "Tại sao hôm nay chưa nên gọi khách hàng này?"
- "Vì sao khách hàng này được ưu tiên?"
- "Yếu tố nào đang ảnh hưởng mạnh nhất đến quyết định?"
- "Khách hàng có cam kết thanh toán nào đang mở không?"
- "Dòng tiền gần đây của khách hàng thế nào?"
- "Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?"

Các câu hỏi về khách hàng cụ thể được trả lời bằng công cụ nghiệp vụ, không
được bịa dữ liệu.

## Mô phỏng

Nút / vùng mô phỏng cho phép thử kịch bản. Mô phỏng không làm thay đổi dữ liệu
gốc.

## Trang này dùng để làm gì

Trả lời câu hỏi: "Khách hàng này như thế nào? Vì sao hệ thống đề xuất hành
động này? Nếu tín hiệu khác thì quyết định đổi thế nào?"