# Kịch bản Demo Chung kết — MSB Trợ lý Thu hồi Nợ

Thời lượng mục tiêu rehearsal: 4 phút 40 giây; giới hạn thi đấu: 5 phút 00 giây.

## Chuẩn bị

- Mở sẵn `/`, `/login`, `/app/priority`, `/app/customer`, `/app/impact`.
- Dùng dữ liệu mô phỏng; không hiển thị mật khẩu hoặc terminal.
- Đăng nhập trước, giữ SYN002846 làm khách hàng trung tâm.
- Kiểm tra Decision Core, mô phỏng và một câu hỏi kiến thức trước giờ demo.

## Timeline và lời thoại

| Thời gian | Màn hình / thao tác | Lời presenter | Điều cần để ý | Giới hạn / dự phòng |
|---|---|---|---|---|
| 00:00–00:30 | Landing `/` | “Trong thu hồi nợ, vấn đề không chỉ là khách hàng nào nợ nhiều nhất. Vấn đề là hôm nay cán bộ nên ưu tiên ai, nên làm gì và vì sao. MSB Trợ lý Thu hồi Nợ giúp tìm cơ hội thu hồi tốt nhất tiếp theo.” | Thesis và đối tượng sử dụng. | Nếu landing chậm, nói phần mở đầu và chuyển sang tab đã tải. |
| 00:30–00:55 | Cuộn tới GreenNode | “Trong bản demo, GreenNode hỗ trợ điều phối các bước, giải thích và tìm tài liệu liên quan. Bộ máy quyết định vẫn giữ quyền xác định kết quả nghiệp vụ.” | Các thành phần GreenNode có vai trò riêng; không thành phần nào tự đổi chính sách. | Nếu section chưa tải, dùng slide kiến trúc dự phòng. |
| 00:55–01:15 | Đăng nhập → Tổng quan | “Đây là không gian tác nghiệp của cán bộ thu hồi nợ: nhìn toàn cảnh, danh sách ưu tiên, khách hàng và tác động dự kiến.” | Sidebar chỉ xuất hiện sau đăng nhập. | Nếu login lỗi, dùng tab app đã xác thực và nói rõ đây là quyền truy cập bản demo. |
| 01:15–01:50 | Danh sách ưu tiên → mở SYN002846 | “Thay vì bắt đầu từ dư nợ lớn nhất, tôi mở khách hàng có cơ hội cần giải thích rõ. Mọi hàng trong bảng đều có thể mở hồ sơ.” | Customer 360, điểm cơ hội, tuyến, hành động và lý do. | Nếu bảng chậm, dùng tab khách hàng đã mở sẵn. |
| 01:50–02:40 | Hồ sơ SYN002846 | “Khách hàng quá hạn 11 ngày, tiền vào 7 ngày là 48 triệu, dòng tiền ròng 30 ngày là 168 triệu, chưa có cam kết thanh toán mở. Khách hàng thuộc tuyến gọi, nhưng tuyến gọi không có nghĩa hôm nay nhất thiết phải gọi. Hệ thống đề xuất chờ khách hàng tự thanh toán và chưa cần liên hệ; điểm cơ hội là 47.” | CALL không đồng nghĩa phải gọi ngay; lý do đến từ dữ liệu đã xác nhận. | Nếu API chậm, chỉ vào dữ liệu đã tải và tiếp tục. |
| 02:40–03:15 | Mở Trợ lý → hỏi quyết định | Hỏi: “Tại sao hôm nay chưa nên gọi khách hàng này?” rồi nói: “Bộ máy đã đưa ra kết quả trước; AI giúp chuyển bằng chứng thành lời giải thích dễ hiểu.” | Giải thích dựa trên DPD, dòng tiền và PTP. | Nếu mô hình chậm: “Kết quả đã được xác nhận; phần giải thích đang được tạo.” Dùng fallback đã hiển thị. |
| 03:15–03:50 | Mô phỏng 48M/168M → 0/0 | “Bây giờ tôi thay đổi bối cảnh: tiền vào 7 ngày và dòng tiền ròng đều bằng 0. Hệ thống tính lại nhất quán: chờ tự thanh toán chuyển thành liên hệ.” | Đây là mô phỏng lại theo quy tắc, không phải dự đoán của AI. | Nếu modal lỗi, dùng ảnh chụp kết quả mô phỏng đã kiểm tra; không tự đọc kết quả ngoài bằng chứng. |
| 03:50–04:20 | Trợ lý → hỏi kiến thức | Hỏi: “CALL và CBS khác nhau thế nào?” rồi nói: “Đây không phải câu hỏi về một khách hàng. Trợ lý tìm trong kho kiến thức GreenNode, mô hình trả lời và hiển thị nguồn tham khảo.” | Câu trả lời có nguồn, tách khỏi quyết định khách hàng. | Khi chờ: “Hệ thống đang tìm tài liệu liên quan trong kho kiến thức GreenNode và tổng hợp câu trả lời có nguồn.” Nếu lỗi, dùng fallback plan. |
| 04:20–04:40 | Impact → close | “Danh mục demo có 3.000 CIF, trong đó 1.740 thuộc tuyến gọi và 32 thuộc tuyến gọi nhưng hiện chưa cần gọi ngay. Phần tác động khoảng 106,5 triệu đồng mỗi năm chỉ là ước tính theo giả định của bản demo, không phải ROI đã đạt. Giá trị là đưa đúng khách hàng, đúng hành động, đúng thời điểm và lý do rõ ràng vào cùng quy trình.” | Nhấn mạnh 3.000 / 1.740 / 32 và phân biệt số đo demo với kết quả thật. | Nếu hết giờ, đọc closing ngay; không bỏ câu “ước tính theo giả định”. |

## Câu chuyển quan trọng

- “AI hỗ trợ hiểu và giải thích; Decision Core giữ quyền quyết định.”
- “RAG trả lời kiến thức hệ thống, không thay đổi CALL/CBS.”
- “Đây là dữ liệu mô phỏng, chưa phải dữ liệu khách hàng thật.”
- “Điểm 47 là điểm ưu tiên, không phải xác suất trả nợ 47%.”

## Kết thúc

“Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.”
