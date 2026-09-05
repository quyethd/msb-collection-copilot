---
document_id: 18-greennode-ai-platform
title: GreenNode AI Platform
section: greennode_platform
topic: GRENNODE
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# GreenNode AI Platform

## Vai trò trong hệ thống

GreenNode không chỉ được dùng để "gọi một mô hình". Trong dự án, GreenNode là
nền tảng AI cung cấp nhiều thành phần:

- **AgentBase** — điều phối công cụ nghiệp vụ, quản lý Agent.
- **MaaS — GLM 5.2** — hỗ trợ giải thích quyết định phức tạp.
- **MaaS — Qwen Flash** — trả lời nhanh các câu hỏi kiến thức (xem ghi chú
  hiện trạng bên dưới).
- **Vector Database (vDB OpenSearch / PostgreSQL pgvector)** — cung cấp ngữ
  cảnh có nguồn cho truy vấn kiến thức (xem ghi chú hiện trạng bên dưới).

## Hiện trạng đã kiểm chứng trong dự án

- **AgentBase runtime**: đã chạy thật (bản cập nhật v7), đã kiểm chứng gọi
  business tool `get_next_best_action`, giữ nguyên quyết định deterministic.
- **MaaS**: kết nối thật với mô hình `z-ai/glm-5.2-hackathon` (GLM 5.2) cho
  đường giải thích quyết định.
- **Qwen Flash**: mô hình `qwen/qwen3.6-flash` đang sẵn sàng trong catalog MaaS
  của tài khoản. Chỉ khẳng định dùng cho RAG sản xuất **sau khi** có bằng chứng
  TASK-011H live.
- **Vector Database**: nền GreenNode cung cấp khả năng vector qua vDB OpenSearch
  (kNN plugin) và PostgreSQL (pgvector). Chỉ khẳng định dùng cho RAG dự án
  **sau khi** được cấp phép provision và có bằng chứng live.

## Mô hình sẵn có trên tài khoản (catalog MaaS)

Catalog MaaS hiện có ba mô hình chat:

- `z-ai/glm-5.2-hackathon`
- `qwen/qwen3.6-flash`
- `google/gemma-4-31b-it`

Trên catalog hiện tại **không có** mô hình embedding sẵn sàng (lời gọi
`/embeddings` với các mô hình chat trả về model-not-found). Do đó embedding
cho RAG cần một mô hình embedding được cấp phép riêng, hoặc dùng adapter local
cho bằng chứng foundation.

## Định hướng kiến trúc

```
                GreenNode AI Platform

       AgentBase           MaaS              VDB
          │           ┌─────┴─────┐           │
          │           │           │           │
     Tool use      GLM 5.2     Qwen Flash   Project
          │        reasoning    knowledge    Knowledge
          │                                   RAG
          ▼
     Decision Core
```

Các thành phần trạng thái "sẽ bổ sung" (Qwen Flash cho knowledge, VDB cho
knowledge RAG) chỉ thể hiện như đã triển khai trên giao diện chính thức sau khi
có bằng chứng live.

## Ranh giới

GreenNode không sở hữu quyết định thu hồi. AI hỗ trợ hiểu quyết định, không
thay đổi quyết định nghiệp vụ.