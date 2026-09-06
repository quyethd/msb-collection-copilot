---
document_id: 24-versioning-and-reliability
title: Phiên bản kiến thức và độ tin cậy
section: versioning
topic: DATA
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
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

- Phiên bản chuẩn hiện tại: **TASK-011H-V2** (Knowledge v2).
- V2 được xây dựng từ current main của dự án — commit
  `617a1ed84e6001155ae87b467bffbf962d3ce3cc` (TASK-011I đã được chấp nhận vào
  main) — phản ánh cấu trúc sản phẩm hiện tại: landing công khai ở `/`, đăng
  nhập demo `/login`, và khu vực ứng dụng sau đăng nhập.
- Mỗi tài liệu trong kho đều mang trường `knowledge_version` và `source_commit`
  để chỉ đúng nguồn.
- `source_commit` chỉ commit tương ứng với nội dung tài liệu.

## Lịch sử phiên bản

- **TASK-011H-V1** (analytic commit `44d24e3c3d2c6277ef2a172e5d8548a1a0402277`)
  là phiên bản nền tảng trước TASK-011I. V1 vẫn được giữ nguyên trong index
  `msb-collection-knowledge-v1` trên GreenNode vDB (V1_PRESERVED) để đối chiếu và
  rollback.
- **TASK-011H-V2** (source commit `617a1ed84e6001155ae87b467bffbf962d3ce3cc`)
  là phiên bản hiện tại, ingest vào index `msb-collection-knowledge-v2` trên
  GreenNode vDB.

## Quy trình cập nhật

- Cập nhật tài liệu đi kèm thay đổi `updated_at` để phản ánh ngày hiệu lực.
- Khi phát hành phiên bản mới, bump phiên bản kiến thức lên (V2, V3...) và cập
  nhật trong toàn bộ kho tài liệu liên quan.
- Khi phát hành phiên bản mới, ingest vào index mới (như
  `msb-collection-knowledge-v2`) thay vì ghi đè bản cũ, để luôn có thể rollback
  về index phiên bản trước.
- Các tài liệu cũ về "đang bị chặn/thất bại" phải được gỡ bỏ hoặc đánh dấu lỗi
  thời.

## Lọc tài liệu lỗi thời (stale filtering)

Trước khi trả lời, hệ thống RAG lọc các nguồn tài liệu không còn hiệu lực:

- ưu tiên tài liệu có `knowledge_version` mới nhất;
- loại các tuyên bố cũ đã bị thay thế;
- nếu phát hiện mâu thuẫn giữa các nguồn cùng phiên bản, ưu tiên nguồn có
  `source_type=curated` và có `implementation_status` tương xứng.
- Với V2, các tuyên bố điều hướng/sản phẩm cũ của V1 (landing trước đây, mục
  sidebar phụ) đã được gỡ khỏi nội dung hoạt động; nội dung hiện tại chỉ phản
  ánh cấu trúc sản phẩm theo TASK-011I.

## Độ tin cậy của nguồn

| Trường              | Giá trị hiện tại                    |
|---------------------|-------------------------------------|
| knowledge_version   | TASK-011H-V2                        |
| source_commit       | 617a1ed84e6001155ae87b467bffbf962d3ce3cc |
| source_type         | curated (chọn lọc, kiểm soát)       |
| implementation_status | IMPLEMENTED / PROVEN / FUTURE / PROTOTYPE_ONLY |
| vDB index (hiện tại) | msb-collection-knowledge-v2         |
| vDB index (V1, giữ nguyên) | msb-collection-knowledge-v1   |

## Nguyên tắc an toàn khi cập nhật

- Không bao giờ để RAG tự sửa kho tài liệu.
- Mọi trả lời phải chỉ rõ phiên bản; nếu thông tin không có trong phiên bản
  hiện tại, nói không biết thay vì đoán.