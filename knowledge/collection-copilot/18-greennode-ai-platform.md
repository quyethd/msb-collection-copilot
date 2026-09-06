---
document_id: 18-greennode-ai-platform
title: GreenNode AI Platform
section: greennode_platform
topic: GRENNODE
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
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
- **Qwen Flash**: mô hình `qwen/qwen3.6-flash` tổng hợp câu trả lời RAG có nguồn
  từ evidence truy xuất trên GreenNode vDB; đã kiểm chứng live trong
  TASK-011H live proof.
- **Vector Database (vDB OpenSearch)**: đã được provisioning và kết nối thật —
  endpoint OpenSearch có plugin kNN, TLS + xác thực; kho kiến thức dự án được
  ingest live và truy xuất live. Phiên bản hiện tại **TASK-011H-V2** lưu trong
  index `msb-collection-knowledge-v2`; index phiên bản V1
  (`msb-collection-knowledge-v1`) được giữ nguyên (V1_PRESERVED). RAG chưa tích
  hợp vào Trợ lý production (COPILOT_INTEGRATION=NO).

## Hiện trạng live (TASK-011H live proof)

- Live ingest: toàn bộ kho kiến thức (phiên bản TASK-011H-V2) được nhúng bằng
  mô hình đa ngôn ngữ local và upsert vào index vDB OpenSearch của GreenNode.
- Live retrieval: truy vấn kNN trên OpenSearch trả về các chunk liên quan; score
  cosine được tính chuẩn hoá để so sánh ngưỡng đã hiệu chỉnh.
- Live Qwen RAG: Qwen Flash `qwen/qwen3.6-flash` trả lời dựa trên evidence truy
  xuất được, kèm citation tới các tài liệu nguồn.
- Kết quả live proof: R@3 = 1.0, MRR = 0.8974, các cổng live đều PASS,
  INFERENCE_ANCHOR = LIVE_GREENNODE_VDB.
- RAG chạy trên GreenNode vDB đã có bằng chứng live, nhưng việc khẳng định dùng
  Qwen Flash cho RAG trong môi trường sản xuất (production) chỉ được thực hiện
  sau khi có kế hoạch tích hợp vào giao diện Trợ lý chính thức. Hiện tại RAG
  chưa tích hợp production (COPILOT_INTEGRATION=NO, DEPLOY=NO).

## Embedding cho RAG

Catalog MaaS hiện có ba mô hình chat:

- `z-ai/glm-5.2-hackathon`
- `qwen/qwen3.6-flash`
- `google/gemma-4-31b-it`

Trên catalog hiện tại **không có** mô hình embedding sẵn sàng. Do đó embedding
cho RAG chạy **local** bằng mô hình đa ngôn ngữ
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều) —
đây không phải dịch vụ embedding do GreenNode host. Khi có mô hình embedding
được cấp phép trên MaaS, có thể chuyển đường embedding sang GreenNode.

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

Qwen Flash (knowledge) và VDB (Project Knowledge RAG) đã được kiểm chứng
**chạy thật** (TASK-011H live proof) với INFERENCE_ANCHOR=LIVE_GREENNODE_VDB;
việc tích hợp vào giao diện Trợ lý production là bước tiếp theo riêng
(COPILOT_INTEGRATION=NO).

## Ranh giới

GreenNode không sở hữu quyết định thu hồi. AI hỗ trợ hiểu quyết định, không
thay đổi quyết định nghiệp vụ. Kho kiến thức RAG chỉ truy vấn tài liệu, không
tự quyết định khách hàng thuộc tuyến CALL hay CBS — tuyến xử lý do Decision Core
xác định từ policy.