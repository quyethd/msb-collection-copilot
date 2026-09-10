# Bộ câu hỏi bảo vệ trước hội đồng

Mỗi câu trả lời ngắn phù hợp khoảng 15–25 giây; câu trả lời sâu tối đa khoảng 60 giây. Không gọi dữ liệu mô phỏng là dữ liệu thật.

## A. Bài toán và khác biệt

### 1. Nếu rule đã quyết định thì cần AI để làm gì?

**Ngắn:** Decision Core bảo đảm nhất quán và kiểm toán. AI giảm gánh nặng nhận biết câu hỏi, chọn công cụ, giải thích, điều tra, mô phỏng và tra cứu kiến thức.

**Sâu:** AI không thay thế chính sách. Nó giúp cán bộ hỏi bằng ngôn ngữ tự nhiên, lấy bằng chứng từ đúng công cụ, hiểu quyết định và thử kịch bản. RAG cũng trả lời kiến thức hệ thống có nguồn. Quyết định nghiệp vụ vẫn thuộc Decision Core.

**Không nói:** AI tự quyết định hoặc AI dự đoán chắc chắn khả năng trả nợ.

### 2. Vậy đây chỉ là rule engine gắn chatbot?

**Ngắn:** Không. Hệ thống điều phối nhiều công cụ, kết hợp Customer 360, dòng tiền, PTP, quyết định, mô phỏng và kho kiến thức có nguồn trong một luồng làm việc.

**Sâu:** Không có trợ lý, cán bộ phải tự mở nhiều màn hình, ghép dữ liệu và diễn giải chính sách. Có trợ lý, câu hỏi được định tuyến đến đúng công cụ, quyết định deterministic được hiển thị trước, AI giải thích sau, và kịch bản thay đổi được chạy lại nhất quán.

**Không nói:** Chatbot tự suy luận toàn bộ nghiệp vụ.

### 3. Sản phẩm khác dashboard ở đâu?

**Ngắn:** Dashboard chủ yếu hiển thị dữ liệu; sản phẩm này ưu tiên khách hàng, đề xuất hành động, giải thích, mô phỏng và trả lời kiến thức có nguồn.

**Sâu:** Bảng ưu tiên là điểm bắt đầu tác nghiệp. Cán bộ có thể đi từ một hàng đến hồ sơ, quyết định, bằng chứng và what-if mà không tự tái dựng logic trong đầu.

**Không nói:** Dashboard truyền thống không có giá trị.

### 4. Vì sao tập trung vào cán bộ thu hồi nợ?

**Ngắn:** Đây là người phải biến dữ liệu thành hành động hàng ngày và chịu áp lực về thời điểm liên hệ.

**Sâu:** Team Leader cũng cần nhìn danh mục và lý do ưu tiên, nhưng workflow đầu tiên tối ưu cho Collection Officer vì họ là người thực hiện hành động.

**Không nói:** Đã chứng minh năng suất trong vận hành thật.

### 5. Sản phẩm giải quyết nỗi đau nào trước tiên?

**Ngắn:** Giảm việc ghép thủ công nhiều tín hiệu để biết hôm nay nên xử lý ai và làm gì.

**Sâu:** Dư nợ và DPD chỉ là một phần. Dòng tiền, PTP và trạng thái liên hệ có thể khiến khách hàng thuộc CALL nhưng chưa cần gọi ngay. Sản phẩm làm mối quan hệ đó rõ ràng hơn.

**Không nói:** Đã giảm chắc chắn số cuộc gọi.

## B. Decision Core và nghiệp vụ

### 6. Tại sao không để LLM tự quyết định?

**Ngắn:** Vì nghiệp vụ thu hồi cần quyết định deterministic, tái lập và kiểm toán được; LLM là xác suất nên chỉ làm tương tác và giải thích.

**Sâu:** Routing, điểm, treatment, channel và timing đi qua chính sách và công cụ đã chấp nhận. LLM không được quyền ghi đè. Đây là ranh giới an toàn quan trọng trong bối cảnh ngân hàng.

**Không nói:** LLM không bao giờ sai.

### 7. RAG có thể thay đổi CALL/CBS không?

**Ngắn:** Không. RAG chỉ truy xuất và tổng hợp kiến thức hệ thống có nguồn.

**Sâu:** Câu hỏi về một khách hàng cụ thể đi vào Customer/Decision/Simulation boundary. Câu hỏi như “CALL và CBS khác nhau thế nào?” mới đi vào Project Knowledge RAG.

**Không nói:** RAG tham gia bỏ phiếu cho quyết định.

### 8. Self-cure có phải AI prediction không?

**Ngắn:** Không trong demo hiện tại. Đây là điều kiện deterministic dựa trên tín hiệu và quy tắc đã chấp nhận.

**Sâu:** WAIT_SELF_CURE nghĩa là tín hiệu hiện tại đáp ứng điều kiện để ưu tiên chờ tự thanh toán; không phải lời hứa khách hàng chắc chắn sẽ trả.

**Không nói:** Self-cure là xác suất thanh toán.

### 9. Điểm 47 nghĩa là khả năng trả nợ 47% à?

**Ngắn:** Không. Đây là điểm Cơ hội thu hồi dùng để xếp ưu tiên, không phải xác suất trả nợ.

**Sâu:** Điểm hỗ trợ so sánh và giải thích thứ tự xử lý trong demo. Nó không được diễn giải thành xác suất nếu chưa có mô hình xác suất và kiểm định tương ứng.

**Không nói:** 47% khả năng thu hồi.

### 10. 32 khách nghĩa là giảm được 32 cuộc gọi?

**Ngắn:** Không. 32 khách trong danh mục mô phỏng thuộc CALL nhưng hiện chưa cần gọi ngay.

**Sâu:** Đây là cơ hội tránh liên hệ chưa cần thiết trong logic demo, không phải số cuộc gọi đã giảm ngoài thực tế.

**Không nói:** Đã giảm 32 cuộc gọi.

### 11. Nếu dòng tiền sai hoặc thiếu thì sao?

**Ngắn:** Hệ thống không cho AI tự bịa dữ kiện. Quy tắc áp dụng trên bằng chứng sẵn có và cần xử lý thiếu dữ liệu theo chính sách.

**Sâu:** Khi dữ liệu không đủ, câu trả lời phải nêu giới hạn hoặc dùng treatment an toàn đã được quy định; AI không lấp khoảng trống bằng trí nhớ.

**Không nói:** AI sẽ ước lượng phần bị thiếu.

### 12. Nếu khách hàng thuộc CALL, tại sao chưa gọi?

**Ngắn:** Tuyến CALL là phương thức xử lý chung; thời điểm hôm nay còn phụ thuộc dòng tiền, PTP và chính sách. SYN002846 thuộc CALL nhưng hiện WAIT_SELF_CURE và NONE.

**Sâu:** DPD 11, inflow 7 ngày 48 triệu, net cashflow 30 ngày 168 triệu và PTP NONE là bằng chứng để Decision Core chọn chờ theo tín hiệu hiện tại.

**Không nói:** Khách hàng chắc chắn sẽ tự trả.

## C. GreenNode và AI

### 13. GreenNode được dùng thật ở đâu?

**Ngắn:** AgentBase điều phối công cụ; GLM 5.2 giải thích phức tạp; Qwen Flash trả lời kiến thức; Vector Database lưu ngữ cảnh dự án có nguồn.

**Sâu:** Hai đường đi tách biệt: quyết định khách hàng đi qua AgentBase và business tools đến Decision Core; câu hỏi kiến thức đi qua embedding local, GreenNode VDB và Qwen. Decision Core vẫn là quyền nghiệp vụ.

**Không nói:** GreenNode tự thay thế toàn bộ nghiệp vụ.

### 14. Nếu GreenNode hoặc model lỗi thì sao?

**Ngắn:** Quyết định nghiệp vụ vẫn ở Decision Core. Phần giải thích hoặc câu trả lời kiến thức có thể fallback hoặc từ chối an toàn.

**Sâu:** Đây là thiết kế tách lỗi: model không thành công không làm mất route/treatment đã xác định. Nếu RAG lỗi, nói rõ lỗi kết nối và tiếp tục bằng chức năng quyết định.

**Không nói:** Hệ thống luôn hoạt động không lỗi.

### 15. Tại sao dùng GLM và Qwen?

**Ngắn:** Hai workload khác nhau: GLM 5.2 cho giải thích quyết định phức tạp; Qwen Flash cho câu hỏi kiến thức nhanh có grounding.

**Sâu:** Đây là phân vai theo tác vụ, không phải tuyên bố model nào luôn tốt hơn. Quyết định không phụ thuộc vào model generation.

**Không nói:** Model này chính xác tuyệt đối hơn model kia.

### 16. AgentBase làm gì ngoài gọi API?

**Ngắn:** AgentBase nhận câu hỏi tự nhiên, điều phối công cụ và thực hiện luồng có kiểm soát.

**Sâu:** AgentBase giúp chọn/điều phối accepted tools và đưa bằng chứng vào phần giải thích. Nó không sở hữu policy; business tool và Decision Core mới xác định kết quả.

**Không nói:** AgentBase tự sửa quy tắc nghiệp vụ.

### 17. Vì sao embedding chạy local?

**Ngắn:** Catalog MaaS được dùng trong triển khai không có endpoint embedding phù hợp, nên embedding multilingual chạy local; GreenNode VDB vẫn là nơi lưu và truy xuất vector live.

**Sâu:** Mô hình local tạo vector 384 chiều bằng fastembed/ONNX. Điều này không có nghĩa embedding chạy trên GreenNode MaaS; VDB và Qwen vẫn là các thành phần GreenNode đã tích hợp.

**Không nói:** GreenNode cung cấp embedding này nếu chưa có bằng chứng.

### 18. RAG trả lời dựa trên nguồn nào?

**Ngắn:** Dựa trên kho kiến thức dự án V2, index `msb-collection-knowledge-v2`, và hiển thị nguồn tham khảo dễ đọc.

**Sâu:** Truy vấn được embed local, tìm trong VDB, lọc theo ngưỡng semantic rồi Qwen tổng hợp trên context. Nếu không đủ tin cậy, hệ thống từ chối.

**Không nói:** Qwen biết mọi tài liệu nội bộ.

## D. RAG và tin cậy

### 19. RAG có hallucination không?

**Ngắn:** Ranh giới giảm rủi ro: facts/decision lấy từ tool và Decision Core; RAG dùng nguồn và từ chối khi confidence thấp.

**Sâu:** Không hứa bằng không tuyệt đối. Thiết kế grounding, citation, semantic threshold và refusal giúp không trả lời kiến thức chung khi kho không đủ bằng chứng.

**Không nói:** Không thể hallucinate.

### 20. Tại sao câu hỏi phở bò bị từ chối?

**Ngắn:** Vì đó là ngoài phạm vi kho kiến thức sản phẩm; hệ thống nói chưa tìm thấy đủ thông tin thay vì dùng kiến thức chung của model.

**Sâu:** Đây là hành vi an toàn và có thể giải thích: không biến Qwen thành chatbot thế giới mở ngoài phạm vi demo.

**Không nói:** Qwen không biết nấu ăn.

### 21. Nếu hỏi “Trang giới thiệu nằm ở đâu?” thì sao?

**Ngắn:** RAG trả lời đúng đường dẫn `/`, là landing công khai, không phải menu ứng dụng.

**Sâu:** Đây là ví dụ knowledge question; nó không truy cập customer decision và có citation từ tài liệu hệ thống.

**Không nói:** Landing là một quyết định nghiệp vụ.

### 22. Câu hỏi kiến thức mất khoảng 10 giây có chậm không?

**Ngắn:** Có, RAG là đường chậm nhất hiện tại; deterministic customer answers vẫn nhanh, RAG không chạy cho mọi request và UI có trạng thái tiến trình.

**Sâu:** Median production khoảng 10.3 giây. Demo ưu tiên grounding và correctness; tối ưu latency là bước engineering tiếp theo, không che giấu số đo.

**Không nói:** 10 giây là tức thì.

## E. Bảo mật và dữ liệu

### 23. Dữ liệu có phải dữ liệu MSB thật không?

**Ngắn:** Không. Demo dùng dữ liệu synthetic.

**Sâu:** Các CIF như SYN002846 phục vụ trình diễn và kiểm thử. Không suy ra hiệu quả vận hành thực tế từ dữ liệu này.

**Không nói:** Đây là khách hàng thật.

### 24. Có lộ prompt hoặc API key không?

**Ngắn:** Không. Credential nằm backend, frontend không chứa secret; response loại bỏ reasoning riêng tư và yêu cầu secret bị từ chối.

**Sâu:** Protected tools có Bearer boundary; RAG chỉ trả answer/citation cần thiết, không trả system prompt, password, token hay vector thô.

**Không nói:** Có thể cho xem key để chứng minh.

### 25. Đây đã là xác thực ngân hàng production chưa?

**Ngắn:** Chưa. Đây là demo application access control với session cookie để trình diễn.

**Sâu:** Demo có HttpOnly, SameSite=Lax và Secure trên HTTPS; session in-memory có thể mất khi backend restart. IAM/RBAC/SSO production là phạm vi khác.

**Không nói:** Bank-grade authentication.

## F. Metrics và tác động

### 26. 106 triệu đồng là lợi ích thật à?

**Ngắn:** Không. Đây là ước tính theo giả định của bản demo, không phải ROI đã đạt.

**Sâu:** Giả định gồm 250 ngày/năm, 100 khách/ngày, 3 phút xem xét thủ công, 0.5 phút với trợ lý, cuộc gọi 3 phút và chi phí 100.000 đồng/giờ. Giá trị mô hình khoảng 106.5 triệu đồng/năm.

**Không nói:** MSB đã tiết kiệm 106 triệu.

### 27. Có tăng thu hồi bao nhiêu phần trăm?

**Ngắn:** Chưa có số liệu vận hành thật nên không tuyên bố uplift.

**Sâu:** Demo đo được logic, thời gian xem xét theo giả định và thứ tự ưu tiên; cần pilot với dữ liệu/đối chứng thật mới đánh giá recovery uplift.

**Không nói:** Tăng X%.

### 28. 3.000 CIF, 1.740 CALL và 32 nghĩa là gì?

**Ngắn:** Đây là danh mục synthetic: 3.000 CIF, 1.740 thuộc CALL, 32 thuộc CALL nhưng chưa cần gọi ngay.

**Sâu:** Các số mô tả output của danh mục và hỗ trợ câu chuyện ưu tiên; không phải thống kê MSB production hay số cuộc gọi đã tránh.

**Không nói:** 32 cuộc gọi được giảm.

## G. Mở rộng và thất bại

### 29. Nếu có 100.000 hoặc 1 triệu khách hàng thì sao?

**Ngắn:** Tách batch deterministic scoring/ranking khỏi assistant interactive; chưa claim benchmark khi chưa đo.

**Sâu:** Có thể tính/rank offline, cache theo state và chỉ dùng interactive path cho hồ sơ/câu hỏi cần tương tác. Cần benchmark hạ tầng và governance trước khi cam kết quy mô.

**Không nói:** Đã scale 1 triệu khách hàng.

### 30. What happens when the network or simulation fails?

**Ngắn:** Không bịa kết quả. Người trình bày chuyển sang ảnh/chứng cứ đã chuẩn bị hoặc nói rõ tính năng đang không khả dụng; quyết định đã xác nhận vẫn giữ nguyên.

**Sâu:** Simulation chỉ thay đổi state synthetic qua accepted route. Nếu lỗi, dừng luồng và giải thích kiến trúc; không tự đọc một kết quả chưa nhận được.

**Không nói:** Giả vờ API đã chạy hoặc đọc số ngoài màn hình.
