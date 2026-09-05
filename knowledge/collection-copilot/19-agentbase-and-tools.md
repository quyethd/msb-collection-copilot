---
document_id: 19-agentbase-and-tools
title: AgentBase và Business Tools
section: agentbase_tools
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

# AgentBase và Business Tools

## Vai trò của AgentBase

AgentBase là runtime tác nhân của GreenNode dùng để **điều phối công cụ nghiệp
vụ**. AgentBase đọc ngữ cảnh/NBA qua tool, điều phối truy vấn và tổng hợp giải
thích tiếng Việt có nguồn.

Luồng:

```text
User → MSB Trợ lý Thu hồi Nợ → GreenNode Agent runtime → accepted tools → dữ liệu → grounded response
```

## Business tools

Các công cụ nghiệp vụ được chấp nhận:

- `get_portfolio` — danh mục.
- `get_customer_360` — ngữ cảnh khách hàng.
- `get_collection_history` — lịch sử tác nghiệp.
- `get_cashflow_intelligence` — tín hiệu dòng tiền.
- `get_collection_policy` — policy.
- `get_recovery_opportunity` — điểm cơ hội thu hồi.
- `get_next_best_action` — hành động tiếp theo (NBA).
- `simulate_decision` — mô phỏng what-if.

## AI vị trí quyết định

- Deterministic Policy/Rule Engine là **source of truth** cho routing, score,
  treatment, channel và timing logic đã khóa.
- GreenNode MaaS/LLM được phép lập kế hoạch tool call, tổng hợp và giải thích;
  không được tự invent hoặc override rule.
- Agent response phải dựa trên structured output từ tools.
- Nếu model output xung đột hard rule, hard rule thắng và conflict phải log.
- What-if phải gọi lại cùng deterministic engine; không để LLM tự "ước lượng"
  score/rank.
- Runtime/platform policy của GreenNode không được dùng thay collection business
  policy.

## Bằng chứng đã kiểm chứng (TASK-011)

- AgentBase gọi `get_next_best_action` trả NBA-300/CALL/WAIT_SELF_CURE/NONE
  cho SYN002846.
- GOLDEN_G02 trả NBA-230/CALL/PTP_FOLLOW_UP/CALL, AgentBase giữ nguyên.
- SYN999999 (khách chưa biết) không trả quyết định, không bịa dữ liệu.
- Yêu cầu override không đổi được quyết định.
- Không lộ reasoning_content, hidden prompt hay chain-of-thought.