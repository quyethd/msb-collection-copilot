# Kế hoạch fallback trong Demo

| Tình huống | Presenter làm gì | Nói gì | Tiếp tục? | Bằng chứng dự phòng |
|---|---|---|---|---|
| Website không tải | Chuyển tab landing đã mở hoặc screenshot | “Tôi chuyển sang bản trình bày đã kiểm tra; kiến trúc không thay đổi.” | Có | Screenshot landing và sơ đồ GreenNode. |
| Login lỗi | Không thử nhiều lần; chuyển app đã xác thực | “Đây là demo access control; tôi tiếp tục phần nghiệp vụ đã nạp sẵn.” | Có | Tab `/app/priority` đã chuẩn bị. |
| Backend lỗi | Không bịa response | “Đường kết nối công cụ đang gặp lỗi; quyết định chưa nhận được nên tôi không đọc thay.” | Có, bỏ phần live | Screenshot Customer/Decision đã kiểm tra. |
| RAG >20 giây | Nói về grounding trong lúc chờ; sau timeout dùng refusal/fallback | “Hệ thống đang tìm tài liệu liên quan trong kho kiến thức GreenNode và tổng hợp câu trả lời có nguồn.” | Có | Screenshot câu trả lời và citation. |
| Qwen lỗi | Hiển thị refusal hoặc bỏ RAG | “Phần tra cứu kiến thức đang gặp lỗi kết nối; quyết định nghiệp vụ vẫn hoạt động độc lập.” | Có | Hero Decision Core và simulation. |
| GreenNode VDB unavailable | Không retry vô hạn | “Kho kiến thức hiện chưa truy cập được; tôi chuyển sang phần quyết định deterministic.” | Có | Decision/What-if evidence. |
| Browser freeze | Chờ tối đa 5 giây, đổi tab | “Tôi chuyển sang màn hình đã tải để giữ đúng mạch demo.” | Có | Tab priority/impact dự phòng. |
| Network unavailable | Dừng live call | “Tôi dùng bản ghi/screenshot đã kiểm tra; không coi đó là kết quả live hiện tại.” | Có | Bộ screenshot offline. |
| Simulation fails | Không tự đọc WAIT→CONTACT | “Mô phỏng chưa trả kết quả nên tôi không khẳng định thay; phần quyết định gốc vẫn có thể xem.” | Có | Screenshot simulation đã kiểm tra trước. |
| Mở nhầm khách hàng | Quay lại priority, chọn SYN002846 | “Tôi chọn lại khách hàng hero để bảo đảm facts nhất quán.” | Có | Direct customer tab nếu có. |

## Nguyên tắc

- Không hiển thị password, token, terminal hoặc log có secret.
- Không gọi dữ liệu demo là dữ liệu thật.
- Không biến screenshot thành bằng chứng live.
- Không tự bịa số, rule, nguồn hay model output.

## Xác nhận bộ screenshot fallback

Bộ screenshot fallback thật đã được tạo từ các lần kiểm tra rendered trước đó và hiện có trong `/tmp`:

- `/tmp/task011h-public-landing-1366.png`
- `/tmp/task011h-public-landing-1440.png`
- `/tmp/task011h-public-landing-1920.png`
- `/tmp/task011h-public-landing-390.png`
- `/tmp/task011h-public-app-drawer.png`
- `/tmp/task011i-app-priority-1366.png`

Các file đều tồn tại và có kích thước khác 0. Bộ này là bằng chứng màn hình đã chụp, không được trình bày như kết quả live tại thời điểm thi. Nên sao chép chúng vào thư mục backup của ban tổ chức trước khi trình bày vì `/tmp` có thể bị dọn sau khi khởi động lại máy.
