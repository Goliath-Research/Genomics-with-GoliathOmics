# DomainProgram Mermaid diagrams

This directory contains standalone Mermaid flowcharts (`.mmd`) generated directly from all **41**
GoliathOmics DomainProgram fixtures (`workflow_engine/domain/fixtures/*.program.json`) using
GoliathApp's generic renderer (`domain.mermaid` / `goliath-cfg render-mermaid`).

* **Browse rendered diagrams online:** [GoliathOmics DomainProgram catalog](https://goliath-research.github.io/GoliathOmics/workflows/)
* **Interactive view in this course:** the **Pack chooser** in Module 3 (`3 - Assays, Analytes & Process Packs/03_in_silico_bisulfite.py`) renders the selected SamplePrep and Study Lifecycle `.mmd` diagrams live with `mo.mermaid(...)`.
* **Embedded in module guides:**
  * Module 3: `sample_prep_rnaseq.mmd`, `sample_prep_proteomics.mmd` (and live in the Pack Chooser for every modality/procedure)
  * Module 5: alignment/quantification/search branches across `sample_prep.mmd`, `sample_prep_rnaseq.mmd`, `sample_prep_proteomics.mmd`
  * Module 7: `sample_prep_remediate.mmd` (two-stage QC gates & remediation)
  * Module 9: `sample_prep.mmd` (full deployed SamplePrep graph) and `event_wait_ack.mmd` (event plane & `WAIT_EVENT`)
  * Module 10: `samd_research.mmd` (MC stability topology) and `study_validation_lifecycle.mmd` (full stability → freeze → model topology)
  * Module 12: all 41 `.mmd` files available for Capstone scenario documentation

## Refreshing from GoliathOmics

```bash
python3 /path/to/GoliathOmics/scripts/generate_domain_program_diagrams.py \
  --emit-mmd-dir diagrams
```

Or directly via GoliathApp's generic CLI:

```bash
goliath-cfg render-mermaid \
  --fixtures-dir /path/to/GoliathOmics/workflow_engine/domain/fixtures \
  --emit-mmd-dir diagrams
```
