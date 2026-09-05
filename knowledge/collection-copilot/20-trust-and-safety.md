---
document_id: 20-trust-and-safety
title: Độ tin cậy và an toàn
section: trust_safety
topic: TRUST
audience: ALL
content_type: business
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Độ tin cậy và an toàn

## Nguyên tắc cốt lõi

1. **Quyết định thuộc về Decision Core deterministic.** AI không được, không
   thể và không có công cụ để tự quyết định routing/score/treatment cho khách
   hàng.
2. **Agent trả lời có căn cứ.** Mọi câu trả lời dựa trên structured output từ
   công cụ nghiệp vụ, không bịa dữ liệu.
3. **Kho kiến thức RAG trả lời có nguồn.** Trả lời từ tài liệu đã được chọn
   lọc, có trích dẫn; không chế ra quy trình không có trong kho.
4. **Không tiết lộ suy luận nội bộ.** Không lộ reasoning_content, hidden
   prompt, chain-of-thought hay thông tin đăng nhập.
5. **Xử lý khách hàng chưa biết an toàn.** Không bịa dữ liệu cho khách chưa
   có trong hệ thống.

## Bằng chứng đã kiểm chứng (TASK-011)

- Decision fidelity: các câu hỏi hợp lệ → tool call đúng → quyết định trả về
  khớp expected (bao gồm SYN002846, GOLDEN_G02).
- Unknown CIF (ví dụ SYN999999): hệ thống xác nhận không tìm thấy, không bịa
  dữ liệu, không trả decision tùy tiện.
- Override guardrail: yêu cầu AI thay đổi NBA bị từ chối, quyết định giữ
  nguyên, có log conflict.
- Không lộ reasoning: private reasoning không xuất hiện trong output.
- Tool use: Agent dùng đúng tool cho đúng intent; tool schemas đúng.

## Guardrails trong thiết kế

- Business policy thắng; conflict log khi AI output xung đột.
- Kho kiến thức có metadata version và source commit để truy vết.
- Bộ lọc an toàn chặn các truy vấn tìm bí mật, thông tin đăng nhập, dữ liệu
  người dùng.
- First-match-wins trong NBA; hard suppression không thể bị phủ quyết.