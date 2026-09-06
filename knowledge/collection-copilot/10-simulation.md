---
document_id: 10-simulation
title: Mô phỏng What-if (Simulation)
section: simulation
topic: SIMULATION
audience: ALL
content_type: business
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Mô phỏng What-if (Simulation)

## Khái niệm

Mô phỏng what-if cho phép cán bộ thử thay đổi một số tín hiệu của khách hàng
và xem quyết định thay đổi như thế nào, **trước khi** quyết định hành động thực
tế.

## Cách hoạt động

1. Hệ thống clone snapshot trạng thái khách hàng trong bộ nhớ (không sửa dữ
   liệu gốc).
2. Áp dụng các thay đổi do người dùng chỉ định.
3. Chạy lại **cùng deterministic engine**.
4. Trả về trước/sau: score, components, treatment, channel, when, rule.

Ví dụ tín hiệu có thể thay đổi trong mô phỏng:

- tiền vào 7 ngày (inflow_7d);
- dòng tiền ròng 30 ngày (net_cashflow_30d);
- trạng thái PTP;
- ngày cam kết thanh toán;
- ngày hành động tiếp theo từ nguồn;
- kết quả nghiệp vụ gần nhất.

## Điểm quan trọng

- Mô phỏng **không làm thay đổi dữ liệu gốc** của khách hàng.
- Mô phỏng dùng cùng engine deterministic, không để LLM tự ước lượng score/rank.
- Mỗi thay đổi phải là một trong các trường được hỗ trợ; trường không hợp lệ bị
  từ chối.

## Ví dụ minh họa

SYN002846 (mô phỏng): thay đổi tiền vào 7 ngày từ 48 triệu đồng xuống 0 và
dòng tiền ròng 30 ngày từ 168 triệu đồng xuống 0 trong kịch bản thử →
hành động chuyển từ "Chờ khách hàng tự thanh toán" sang "Liên hệ khách hàng".

## Ranh giới

- Mô phỏng trạng thái cụ thể của một khách hàng là quyết định what-if
  (SIMULATION_REQUIRED), cần công cụ nghiệp vụ, không phải kiến thức RAG.
- Kết quả mô phỏng không được dùng như quyết định đã có hiệu lực.