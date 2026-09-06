---
document_id: 11-overview-page-guide
title: Hướng dẫn trang Tổng quan
section: user_guide
topic: USER_GUIDE
audience: COLLECTION_OFFICER
content_type: product_guide
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Hướng dẫn trang Tổng quan

## Vị trí trong sản phẩm

Trang Tổng quan nằm trong **khu vực ứng dụng** (sau khi đăng nhập, đường dẫn
`/app`). Đây là trang đầu tiên người dùng thấy sau đăng nhập; sidebar khu vực
ứng dụng gồm: Tổng quan, Danh sách ưu tiên, Khách hàng, Tác động dự kiến và
Trợ lý Thu hồi Nợ.

## Mục đích

Trang Tổng quan cho cán bộ **toàn cảnh danh mục thu hồi hôm nay**: tình trạng
danh mục, tuyến xử lý và các điểm cần chú ý.

## Nội dung chính

- **Chỉ số tổng quan**: số khách hàng trong danh mục, số hồ sơ được trả về,
  số khách thuộc tuyến CALL, số khách có quyết định.
- **Phân bổ hành động hôm nay**: nhóm hành động đề xuất (chờ, theo dõi cam kết,
  liên hệ, nhắc thanh toán…).
- **Phân bổ tuyến xử lý**: tỷ lệ CALL / CBS.
- **Điểm cần chú ý hôm nay**: số hồ sơ có hạn chế liên hệ, số hồ sơ chưa cần
  liên hệ theo đề xuất hiện tại.

## Lưu ý

Các phân bổ trên màn hình chỉ phản ánh **các hồ sơ được API trả về**(danh sách
20 hồ sơ đầu), không tính trên toàn bộ danh mục 3.000 khách hàng mô phỏng. Số
liệu dùng trong bản demo là dữ liệu mô phỏng.

## Trang này dùng để làm gì

Trả lời câu hỏi: "Danh mục hôm nay ra sao? Có gì cần chú ý?" Để xác định cụ
thể khách hàng nào xử lý trước, dùng trang Danh sách ưu tiên.