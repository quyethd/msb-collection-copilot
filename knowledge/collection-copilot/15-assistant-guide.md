---
document_id: 15-assistant-guide
title: Hướng dẫn Trợ lý Thu hồi Nợ
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

# Hướng dẫn Trợ lý Thu hồi Nợ

## Vai trò

Trợ lý Thu hồi Nợ là giao diện hội thoại giúp cán bộ **tương tác tự nhiên** với
hệ thống. Trợ lý hiểu câu hỏi, chọn đúng công cụ nghiệp vụ, lấy quyết định từ
Decision Core rồi giải thích dựa trên bằng chứng.

## Hiện trạng

Trợ lý hiện có gắn với bối cảnh khách hàng đang xem và hỗ trợ **Hỏi về quyết
định**: giải thích quyết định hiện tại, tóm tắt tình trạng, yếu tố có thể thay
đổi quyết định, điều tra ngữ cảnh, mô phỏng tình huống.

Ví dụ câu hỏi Trợ lý trả lời được (dựa trên quyết định đã xác định và dữ liệu
khách hàng hiện có):

- "Tại sao hôm nay chưa nên gọi khách hàng này?"
- "Vì sao khách hàng này được ưu tiên?"
- "Khách hàng có cam kết thanh toán nào đang mở không?"
- "Dòng tiền gần đây của khách hàng thế nào?"
- "Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?"

## Hướng phát triển (TASK-011H)

Trợ lý được định hướng mở rộng sang hai lớp câu hỏi:

1. **Hỏi về quyết định** — Decision Core xác định hành động, GreenNode AI giải
   thích.
2. **Hỏi về nghiệp vụ / cách sử dụng sản phẩm** — GreenNode Vector Database
   tìm tài liệu liên quan, Qwen Flash trả lời dựa trên nguồn.

Lớp kiến thức này chưa được kết nối chính thức vào giao diện Trợ lý trong
TASK-011H (bản TASK-011G đang được phát triển song song); TASK-011H cung cấp
nền tảng RAG có thể tích hợp sau.

## Ranh giới an toàn

- Trợ lý không tự thay đổi quyết định nghiệp vụ.
- Trợ lý không bịa dữ liệu khách hàng chưa biết.
- Trợ lý không tiết lộ lý do suy luận nội bộ.
- Câu hỏi về quyết định của một khách hàng cụ thể phải đi qua công cụ nghiệp
  vụ, không phải kiến thức chung.