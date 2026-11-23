# Evidence Package Template

*Genomics with GoliathOmics · Goliath Research Academy* · [Module 12](12_content.md)

One package per study run. Every "Source of record" is a table and key, a file and sha256, a
commit SHA or a CI run URL. Leave a row empty and list it under **Gaps** rather than guess.

## 1. Identification

| Item | Value | Source of record |
|---|---|---|
| Study | `academy_ena_srr28293403` | `cfg` study row |
| Site / profile | `academy_lab_site` / | `cfg` site and profile rows |
| Subject (public) | HG00621 (BioSample SAME123082) | `omics_clinical` patient; ENA |
| Run | SRR28293403 | ENA run record; `data/fixtures/manifest.json` |
| GoliathApp / GoliathOmics commits | | `lab/pins.env` |

## 2. Configuration

| Item | Value | Source of record |
|---|---|---|
| Resolved config hash | | `cfg` `content_hash` |
| Overlay provenance | | Module 8 `resolve()` output |
| Guardrail thresholds | | schema defaults + overrides |

## 3. Execution

| Item | Value | Source of record |
|---|---|---|
| Start request and status history | | `cfg.study_start_request` (in-place today, see gap matrix) |
| Workflow instance and node executions | | `wf` tables (H3) |
| Action logs | | `/work` JSONL + sha256 |

## 4. Results and QC

| Item | Value | Source of record |
|---|---|---|
| QC metrics and decisions | | QC report + guardrail evaluation |
| Feature matrix | | feature_store HDF5 + sha256 |

## 5. History integrity

| Item | Value | Source of record |
|---|---|---|
| `fn_ledger_verify_all()` result | | query output, time (UTC) |
| Exported checkpoint | | `fn_ledger_checkpoint()` export + sha256 |
| Approvals / signatures | | H4 |

## 6. Claim boundary

State the lifecycle stage and that clinical performance claims are blocked before
`pivotal_validation` (`RegulatoryLifecycleConfig`).

## 7. Gaps

List every empty row above and the platform change that closes it.
