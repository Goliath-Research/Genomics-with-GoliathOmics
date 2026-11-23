# Module 5: Alignment, Quantification & Search

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

**Notebook:** `05_three_letter_alignment.py` · **Support code:** `module_05_alignment.py` ·
**Sources:** GoliathOmics `docs/usage/alignment-engines.md`, `docs/operators/start-sample-prep.md`,
`docs/usage/20-rnaseq-process-pack.md`, `docs/usage/22-proteomics-process-pack.md`,
`workflow_engine/domain/pipeline_profiles.py`, GoliathAlign `README.md`

## Goal

Know how each modality turns raw data into placed or identified molecules, and how GoliathOmics
picks the path from configuration rather than code.

## 5.1 Concepts

* **Alignment** finds where a read came from: seed, extend, score. **MAPQ** expresses confidence;
  multi-mapping reads get low MAPQ; paired-end reads add an expected insert size.
* **Bisulfite alignment** compares in three-letter space: index C→T (and G→A) converted references
  and convert reads the same way (the bwa-meth approach). Methylation is then read off by comparing
  the original read with the reference (Module 6).
* **Graph alignment** maps to a pangenome (many haplotypes) to reduce reference bias, then
  **surjects** hits back to linear GRCh38 coordinates when a linear output is needed.
* **Quantification** (RNA-seq) either aligns spliced reads to the genome and counts per gene
  (STAR) or pseudo-aligns to transcripts and estimates abundance (kallisto).
* **Database search** (proteomics) matches spectra to peptides from a protein FASTA (DIA-NN for
  DIA, Sage for DDA), optionally rescored by a deep-learning model (Prosit); **de novo**
  sequencing (Casanovo) reads peptides without a database.

## 5.2 The methylation align paths

SamplePrep has three `alignmentMode` values and four executors
(`docs/usage/alignment-engines.md`):

| `alignmentMode` | Action | Engine | Typical procedure |
|---|---|---|---|
| `linear` | `sample.parabricks_fq2bam` | Clara Parabricks `fq2bam_meth` (`actionConfig.parabricks.engine: parabricks`) | `buffy_wgbs_linear_gene_fc` |
| `linear` | `sample.parabricks_fq2bam` | GoliathAlign (`engine: mojo`, CPU possible) | `buffy_wgbs_linear_mojo_gene_fc` |
| `pangenome` | `sample.parabricks_giraffe` | Clara Parabricks Giraffe (stock, non-bisulfite) | — |
| `pangenome_wgbs` | `sample.methylgrapher_wgbs_align` → `…_extract` | methylGrapher (`align_engine` `cpu_vg` default, `gpu_giraffe`, `mojo_giraffe`) | `buffy_wgbs_pangenome_gene_fc` |

The path is chosen by **configuration**: procedure → `alignmentMode` → the scope flags
`usePangenome` / `useWgbsPangenome` (`seed_pipeline_scope_flags` in `pipeline_profiles.py`). The
DomainProgram branches on those flags. Failure policy is explicit: a failed `pangenome_wgbs` sample
stops; it is never silently re-run on another engine. The lab study in this course pins
`buffy_wgbs_linear_gene_fc`, so only the linear path is selected.

## 5.3 RNA-seq and proteomics paths

| Modality | Switch | Values → action |
|---|---|---|
| RNA-seq | `actionConfig.rna_align.quant_mode` | `star` (default) → `sample.parabricks_rna_fq2bam`; `kallisto` → `sample.kallisto` |
| Proteomics | `actionConfig.proteomics_quant.ingest_mode` | `dia` (default) → `sample.diann` (+ `sample.dl_rescore` when `rescore: true`); `dda` → `sample.sage` (CPU); `panel` → `sample.ingest_panel` |

Same pattern every time: a typed configuration value, a derived flag, a branch in the program.
Adding an engine means a new action and a new value, not a new platform.

## 5.4 GPU is a deployment detail

Parabricks, DIA-NN, Prosit and Casanovo run on GPU workers; Sage, panel ingest and the GoliathAlign
CPU path run on CPU workers. The course never requires a GPU. Workers are paid infrastructure:
nothing in this course starts one.

## Lab sequence

1. Open the notebook and move the read start and methylated share. Record mismatches for naive vs
   three-letter placement at 0%, 50% and 100% methylation.
2. In `psql`, find the actions behind each path:

   ```sql
   SELECT action_name, execution_mode FROM wf.workflow_action
   WHERE action_name IN ('sample.parabricks_fq2bam','sample.parabricks_giraffe',
     'sample.methylgrapher_wgbs_align','sample.parabricks_rna_fq2bam','sample.kallisto',
     'sample.diann','sample.sage','sample.ingest_panel','sample.casanovo')
   ORDER BY 1;
   ```

3. Open `.lab-src/GoliathOmics/workflow_engine/domain/fixtures/sample_prep_rnaseq.program.json`
   and find the branch on `useKallisto`.

## Practice

* Why does an unmethylated read look worse to a naive aligner than a methylated one?
* A customer switches proteomics from DIA to an Olink panel. Which value changes? Which action runs?
  Which QC still applies?
* Why must a failed pangenome sample not fall back to Clara automatically? (Hint: Module 8, the
  configuration is part of the result.)

## Evidence to submit

* Your mismatch table from the notebook and the query output.

## Handoff to Module 6

Placed reads and identified peptides are not yet data you can analyze. Module 6 turns them into
per-sample feature matrices.
