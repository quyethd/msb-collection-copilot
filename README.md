# MSB Collection Decision Copilot — TASK-001

This repository currently implements only the deterministic synthetic-data foundation from TASK-001. It does not implement the policy engine, recovery scoring, treatments, Agent/GreenNode integration, frontend, AEV, ML, or real MSB integrations.

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

## Technical assumptions

- UTC is used for deterministic timestamps.
- Monetary values are integer VND serialized into PostgreSQL-compatible numeric columns.
- Blank CSV values map to SQL `NULL` when loaded.
- Synthetic phone identifiers are deliberately non-dialable strings and recording fields are blank.
- `docs/spec-v1/README.md` is the `SPEC_README.md` referenced by TASK-001; the handoff document describes copying that file under the latter name.

