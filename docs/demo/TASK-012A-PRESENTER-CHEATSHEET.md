# Presenter Cheat Sheet — Một trang

## Mở đầu

Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.

## Hero SYN002846

- DPD: **11**
- Inflow 7 ngày: **48M VND**
- Net cashflow 30 ngày: **168M VND**
- PTP: **NONE**
- Route: **CALL**
- Treatment: **WAIT_SELF_CURE** — Chờ khách hàng tự thanh toán
- Channel: **NONE** — Chưa cần liên hệ
- Recovery Opportunity: **47**, không phải xác suất 47%
- Key line: **Thuộc tuyến gọi không có nghĩa hôm nay nhất thiết phải gọi.**

## What-if

- 48M / 168M → **0 / 0**
- WAIT_SELF_CURE → **CONTACT**
- **Chờ tự thanh toán** → **Liên hệ khách hàng**
- “Context đổi thì hệ thống tái tính nhất quán.”

## GreenNode

- **AgentBase trong bản demo:** hỗ trợ điều phối công cụ nghiệp vụ; không tự quyết định chính sách.
- **GLM 5.2:** giải thích quyết định phức tạp.
- **Qwen Flash:** trả lời kiến thức có grounding.
- **Vector Database:** ngữ cảnh dự án và nguồn tham khảo.
- **Decision Core:** quyền xác định routing, score, treatment, channel, timing.
- Câu tin cậy: “GreenNode AI hỗ trợ phân tích, giải thích và tra cứu kiến thức; Bộ máy quyết định giữ quyền xác định kết quả nghiệp vụ.”

## Impact wording

3.000 CIF · 1.740 CALL · 32 CALL nhưng chưa cần gọi ngay. Giá trị khoảng 106.5M/năm chỉ là **ước tính theo giả định của bản demo**, không phải ROI thật, không phải giảm 32 cuộc gọi.

## RAG wait

“Hệ thống đang tìm các tài liệu liên quan trong kho kiến thức GreenNode và tổng hợp câu trả lời có nguồn.”

## Top 10 câu hỏi nguy hiểm

1. Rule rồi cần AI làm gì?
2. Chỉ là rule engine + chatbot?
3. Vì sao không để LLM quyết định?
4. GreenNode dùng thật ở đâu?
5. Model/VDB lỗi thì sao?
6. Vì sao GLM và Qwen?
7. RAG đổi CALL/CBS được không?
8. Self-cure có phải prediction không?
9. Điểm 47 là 47% à?
10. 32 khách có nghĩa giảm 32 cuộc gọi à?

## Kết

AI hỗ trợ hiểu, giải thích, mô phỏng và tra cứu. Decision Core giữ quyết định. Dữ liệu demo là synthetic.
