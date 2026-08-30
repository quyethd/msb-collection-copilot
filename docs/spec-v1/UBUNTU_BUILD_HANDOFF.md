# UBUNTU_BUILD_HANDOFF

## Mục tiêu
Đây là checklist trước khi copy bộ spec lên Ubuntu/server để bắt đầu build.

## 1. Copy bundle
Giải nén project spec vào root của repo, ví dụ:

```bash
mkdir -p docs/spec-v1
cp PRODUCT_SPEC_V1.md RULE_BASE_V1.md SYNTHETIC_DATA_SPEC.md GOLDEN_SCENARIOS_V1.md docs/spec-v1/
cp README.md docs/spec-v1/SPEC_README.md
```

## 2. GreenNode prerequisites
Bộ skill GreenNode phải được cài/import theo tài liệu workshop/repo chính thức.

Credentials chỉ set bằng environment/secrets:

```bash
export GREENNODE_CLIENT_ID="..."
export GREENNODE_CLIENT_SECRET="..."
```

Không commit `.env`, API key hoặc secret.

## 3. Build gate
Không làm UI/Agent trước khi:
- synthetic generator chạy;
- policy/scoring engine chạy;
- 20 golden deterministic scenarios pass.

## 4. AgentBase gate
Sau deterministic PASS:
- setup/validate AgentBase;
- cấu hình MaaS;
- expose 7 business tools;
- deploy runtime;
- xem logs/trace;
- chạy 5 HERO scenarios qua Agent.

## 5. Coding agent instruction
Dùng nguyên văn:

> Read all files under `docs/spec-v1/` before implementing. Treat them as the business contract. Do not invent, modify, optimize, reinterpret, or add collection business rules. If a requirement is missing, stop and report it as UNKNOWN instead of guessing. Implement one task at a time and run the relevant tests before proceeding.

## 6. First build task
`TASK-001 — Synthetic Data Generator`

Không bắt đầu bằng frontend.
