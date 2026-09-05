---
document_id: 24-versioning-and-reliability
title: Phiên bản kiến thức và độ tin cậy
section: versioning
topic: DATA
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Phiên bản kiến thức và độ tin cậy

## Tại sao cần versioning

Kiến thức dự án thay đổi theo thời gian: quy tắc được cập nhật, các task mới
hoàn thành, các số liệu được ghi nhận lại. Kho kiến thức RAG phải gắn phiên bản
để:

- truy vết được trả lời về đúng bản tài liệu;
- ngăn trả lời từ tài liệu cũ đã hết hiệu lực;
- đảm bảo chất lượng ổn định giữa các lần cập nhật.

## Phiên bản kiến thức (Knowledge Version)

- Phiên bản chuẩn hiện tại: **TASK-011H-V1** (hay KNowledge v1).
- Mỗi tài liệu trong kho đều mang trường `knowledge_version` và `source_commit`
  để chỉ đúng nguồn.
- `source_commit` chỉ commit tương ứng với nội dung tài liệu.

## Quy trình cập nhật

- Cập nhật tài liệu đi kèm thay đổi `updated_at` để phản ánh ngày hiệu lực.
- Khi phát hành phiên bản mới, bump phiên bản kiến thức lên (V2, V3...) và cập
  nhật trong toàn bộ kho tài liệu liên quan.
- Các tài liệu cũ về "đang bị chặn/thất bại" (như các tuyên bố cũ của TASK-011
  BLOCKED/FAIL) phải được gỡ bỏ hoặc đánh dấu lỗi thời; hiện tại TASK-011 là
  PASS.

## Lọc tài liệu lỗi thời (stale filtering)

Trước khi trả lời, hệ thống RAG lọc các nguồn tài liệu không còn hiệu lực:

- ưu tiên tài liệu có `knowledge_version` mới nhất;
- loại các tuyên bố cũ đã bị thay thế;
- nếu phát hiện mâu thuẫn giữa các nguồn cùng phiên bản, ưu tiên nguồn có
  `source_type=curated` và có `implementation_status` tương xứng.

## Độ tin cậy của nguồn

| Trường              | Giá trị hiện tại                    |
|---------------------|-------------------------------------|
| knowledge_version   | TASK-011H-V1                        |
| source_commit       | 44d24e3c3d2c6277ef2a172e5d8548a1a0402277 |
| source_type         | curated (chọn lọc, kiểm soát)       |
| implementation_status | IMPLEMENTED / PROVEN / FUTURE / PROTOTYPE_ONLY |

## Nguyên tắc an toàn khi cập nhật

- Không bao giờ để RAG tự sửa kho tài liệu.
- Mọi trả lời phải chỉ rõ phiên bản; nếu thông tin không có trong phiên bản
  hiện tại, nói không biết thay vì đoán.