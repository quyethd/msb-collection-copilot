---
document_id: 15-assistant-guide
title: Hướng dẫn Trợ lý Thu hồi Nợ
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

## Lớp kiến thức (TASK-011H live)

Trợ lý có hai lớp câu hỏi:

1. **Hỏi về quyết định** — Decision Core xác định hành động, GreenNode AI giải
   thích.
2. **Hỏi về nghiệp vụ / cách sử dụng sản phẩm** — GreenNode Vector Database
   (OpenSearch) tìm tài liệu liên quan trong kho kiến thức dự án, Qwen Flash
   trả lời dựa trên nguồn.

Lớp kiến thức RAG đã được kiểm chứng **chạy thật** trên GreenNode vDB
(TASK-011H live proof, INFERENCE_ANCHOR=LIVE_GREENNODE_VDB): ingest và truy
xuất live, câu trả lời Qwen Flash có nguồn (citation). Phiên bản kiến thức
hiện tại là **TASK-011H-V2**. RAG **chưa được tích hợp vào giao diện Trợ lý
production** (COPILOT_INTEGRATION=NO) — đây là nền tảng sẵn sàng để tích hợp
trong bước tiếp theo.

## Ranh giới an toàn

- Trợ lý không tự thay đổi quyết định nghiệp vụ.
- Trợ lý không bịa dữ liệu khách hàng chưa biết.
- Trợ lý không tiết lộ lý do suy luận nội bộ.
- Câu hỏi về quyết định của một khách hàng cụ thể phải đi qua công cụ nghiệp
  vụ, không phải kiến thức chung.