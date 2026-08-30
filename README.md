# MSB Collection Decision Copilot — TASK-001 through TASK-003

This repository implements the deterministic synthetic-data foundation from TASK-001, policy/rule engine from TASK-002, and approved prototype Recovery Opportunity scoring from TASK-003. It does not implement treatment/channel/time recommendations, Agent/GreenNode integration, frontend, AEV, ML, or real MSB integrations.

All generated identifiers and content are visibly synthetic. The default configuration creates exactly 3,000 CIFs, including stable `GOLDEN_G01` through `GOLDEN_G20` fixtures. `G01`–`G05` are HERO fixtures. Normal records use correlated archetypes (stable income, contactability, and operation/payment patterns); these are prototype fixtures and do not claim to represent MSB’s population.

## Requirements

- Python 3.10 or newer
- No runtime third-party packages
- PostgreSQL is not required to generate or validate CSVs. The compatible schema is in `sql/001_synthetic_schema.sql` for later local loading.

## Generate

```bash
PYTHONPATH=src python -m msb_synthetic.generator
```

Output is written to `build/synthetic-data/` and includes one normalized CSV per required entity plus `generation_manifest.json`. The default seed is `20260828` and the default evaluation date is `2026-08-28`. Both can be configured:

```bash
PYTHONPATH=src python -m msb_synthetic.generator \
  --output build/synthetic-data \
  --seed 20260828 \
  --reference-date 2026-08-28 \
  --population 3000
```

`generated_at` is intentionally nondeterministic and excluded from logical comparison. `deterministic_digest` covers the ordered logical CSV content. PTP BROKEN validation uses the configurable demo default of one grace day; the generator stores source facts and does not encode a real MSB grace policy.

## Validate and test

```bash
PYTHONPATH=src python -m msb_synthetic.validate build/synthetic-data
PYTHONPATH=src python -m unittest discover -s tests -v
```

The validator checks scale, foreign keys, monetary constraints, manifest metadata, the mandated G09–G15/G19/G20 contracts, and input evidence for every G01–G20 fixture. Expected treatment/rule metadata is stored for future engines but is not computed or enforced as a policy decision in TASK-001.

## Evaluate TASK-002 policy facts

Generate TASK-001 data first, then run:

```bash
PYTHONPATH=src python -m msb_policy.cli \
  --input build/synthetic-data \
  --output build/policy-results
PYTHONPATH=src python -m msb_policy.validate \
  --input build/synthetic-data \
  --output build/policy-results/golden_policy_validation.json
```

The engine emits one structured JSONL result per CIF. Its deterministic pipeline is aggregation → base routing → explicit synthetic challenge override → no hard suppression (none is defined in the locked rule base) → PTP and source next-action facts → baseline benchmark ordering. The default PTP grace period is the configurable one-day prototype value and can be changed with `--ptp-grace-days`; it is not represented as production MSB policy.

Policy results keep technical call statuses separate from business operation outcomes. They contain no Recovery Opportunity score, treatment recommendation, optimized channel, or optimized contact time.

## Evaluate TASK-003 Recovery Opportunity

TASK-003 uses the explicit prototype formulas in `TASK-003_SCORING_CONTRACT.md`. Generate TASK-001 data first, then run:

```bash
PYTHONPATH=src python -m msb_recovery.cli \
  --input build/synthetic-data \
  --output build/recovery-opportunity
PYTHONPATH=src python -m msb_recovery.validate \
  --input build/synthetic-data \
  --output build/recovery-opportunity/golden_recovery_validation.json
```

The deterministic JSONL output contains source-derived features, component evidence, score traces, baseline rank, Recovery Opportunity rank, and immutable TASK-002 routing facts. Missing evidence is marked `MISSING` and contributes zero; it is not treated as negative behavior. Strategic Adjustment is zero for every V1 record. These synthetic prototype scores are not production payment probabilities or real MSB performance metrics.

## Technical assumptions

- UTC is used for deterministic timestamps.
- Monetary values are integer VND serialized into PostgreSQL-compatible numeric columns.
- Blank CSV values map to SQL `NULL` when loaded.
- Synthetic phone identifiers are deliberately non-dialable strings and recording fields are blank.
- `docs/spec-v1/README.md` is the `SPEC_README.md` referenced by TASK-001; the handoff document describes copying that file under the latter name.
