---
document_id: 12-priority-page-guide
title: Hướng dẫn trang Danh sách ưu tiên
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

# Hướng dẫn trang Danh sách ưu tiên

## Mục đích

Trang Danh sách ưu tiên trả lời câu hỏi: **"Hôm nay nên xử lý ai trước?"**

## Nội dung chính

Danh sách khách hàng ưu tiên hôm nay với các cột:

- Mã khách hàng (CIF);
- Dư nợ;
- Quá hạn (DPD);
- Điểm cơ hội thu hồi;
- Tuyến xử lý (CALL / CBS);
- Hành động đề xuất;
- Lý do chính;
- Nút Chi tiết mở hồ sơ khách hàng.

## Bộ lọc

- Tìm theo mã khách hàng.
- Lọc theo tuyến xử lý.
- Lọc theo hành động đề xuất.

## Lưu ý

- Danh sách giữ thứ tự xếp hạng hiện có và chỉ phản ánh các hồ sơ được API trả
  về.
- Lý do chính hiển thị các dữ kiện đang có (DPD, điểm cơ hội), không bịa thêm.
- Có lối tắt mở hồ sơ demo SYN002846 ngay cả khi khách này không nằm trong danh
  sách trả về.

## Trang này dùng để làm gì

Xác định khách hàng nên ưu tiên xử lý trước dựa trên cơ hội thu hồi và hành
động được đề xuất, sau đó mở chi tiết để xem ngữ cảnh đầy đủ.