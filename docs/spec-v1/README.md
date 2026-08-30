# SPEC LOCK V1

Thứ tự build bắt buộc:

1.  PRODUCT_SPEC_V1.md
2.  RULE_BASE_V1.md
3.  SYNTHETIC_DATA_SPEC.md
4.  GOLDEN_SCENARIOS_V1.md
5.  Synthetic Data Generator
6.  Policy/Rule Engine
7.  Recovery Opportunity Engine
8.  Golden automated tests
9.  Baseline vs Copilot
10. GreenNode tools/Agent
11. What-if
12. Demo UI
13. AgentBase deploy
14. Benchmark + AEV + hardening

**Gate:** Codex chỉ bắt đầu implementation sau khi 4 spec được chấp
nhận.

## GREENNODE BUILD PATH

### Required development path
1. Spec lock.
2. Synthetic generator.
3. Deterministic policy/scoring engine.
4. Golden tests.
5. GreenNode Agent tools.
6. `/agentbase-wizard` setup/validate.
7. `/agentbase-llm` MaaS config.
8. `/agentbase` runtime wiring.
9. `/agentbase-deploy`.
10. `/agentbase-monitor` logs/trace.
11. UI + benchmark + AEV + demo hardening.

### Environment contract

Credentials MUST be environment variables/secrets, never committed:

```bash
export GREENNODE_CLIENT_ID="..."
export GREENNODE_CLIENT_SECRET="..."
```

Before deployment:
- validate project;
- run deterministic test suite;
- run 20 golden scenarios;
- run 5 Agent HERO scenarios;
- verify no secrets in repo.

## CODING TOOL POLICY

Coding tool is replaceable; business contract is not.

Allowed:
- Codex CLI on Ubuntu.
- GreenNode MaaS coding-capable model via a coding agent/tool.
- OpenClaw/Aider/other coding agent when connected to GreenNode MaaS and constrained by these specs.

Regardless of tool:
- no rule invention;
- small task-by-task commits/checkpoints;
- tests before next task;
- generated code must remain reproducible from repo + README.
