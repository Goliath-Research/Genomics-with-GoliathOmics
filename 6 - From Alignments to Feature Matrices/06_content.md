# Module 6: From Alignments to Feature Matrices

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

**Notebook:** `06_feature_matrices.py` · **Support code:** `module_06_features.py` ·
**Sources:** GoliathExtractor `README.md`, GoliathOmics `workers/methyl_worker/extract_runner.py`,
`packages/omicsfeatures/omics_features/feature_store.py`, `packages/rnaexpress`,
`packages/proteomicsfeatures`, `docs/usage/20-…`, `22-…`, `docs/usage/03-sample-prep-and-qc.md`

## Goal

Turn placed reads or identified peptides into one value per feature per sample, and know the file
contract each modality hands to the study lifecycle.

## 6.1 Methylation extraction

For each cytosine, count reads that show C (methylated) and T (unmethylated). Filters decide which
reads and bases count. GoliathExtractor (a MethylDackel fork, MIT) defaults: CpG always; MAPQ ≥ 30;
base quality (Phred) ≥ 20; coverage ≥ 4; CHG/CHH only with `-G` / `-H`. M-bias (biased calls near
read ends) and strand handling are the classic pitfalls.

| Action | Path | Outputs in `sampleDir` |
|---|---|---|
| `sample.methyl_extract` | linear and stock pangenome | `{chr}-CG.h5`, optional `{chr}-CG.patterns.h5`, `{sample_id}.extraction_manifest.json`, `{sample_id}.timing.json` |
| `sample.methylgrapher_wgbs_extract` | WGBS pangenome | same contract |

The per-position records follow the `MethylSample` layout used by `methyl_utils`
(`pos`, `mC`, `uC`, …). From them: **beta** = mC / (mC + uC) where coverage passes; **CpG-weighted
mean coverage**; **global methylation level**. Plants add CHG and CHH matrices.

## 6.2 RNA-seq and proteomics

| Modality | Action | Normalization | File |
|---|---|---|---|
| RNA-seq | `sample.register_expression` | STAR gene counts, or kallisto transcripts aggregated to genes via `tx2gene` | `{sample_id}.expression.h5` (`count`, `tpm`) |
| Proteomics (DIA/DDA) | `sample.register_abundance` | DIA-NN or Sage protein quantities | `abundance.h5` |
| Proteomics (panel) | `sample.ingest_panel` | Olink NPX, SomaScan RFU or an open matrix | `abundance.h5` |

At the study level, `pipeline.rna_de_select` builds a samples × genes **log-CPM** matrix, and
`pipeline.protein_de_select` builds samples × proteins with **log2 + per-sample median
normalization + per-protein minimum imputation**. Both then use the same classifier.

## 6.3 One contract: samples × features

`omics_features.feature_store` writes per-sample `{sample_id}.{kind}.h5` files with datasets
`feature_id` and `value`, optional aligned vectors (for example `tpm`), and attributes `source`,
`kind`, `n_features`, `sample_id`. The reader still accepts legacy RNA files with `gene_id` +
`count`. A new modality that writes this contract inherits the whole downstream lifecycle.

## Lab sequence

1. Open the notebook. Change the coverage threshold and record how many CpGs keep a beta value.
2. Check the RNA and proteomics tables by hand for one row.
3. Run `pytest tests/test_module_06.py -v`. One test writes a feature file with the course helper
   and, when the pinned GoliathOmics source is present (`.lab-src`), reads it back with the
   **official** `read_feature_datasets`, proving the course file matches the platform contract.

## Practice

* Why is beta undefined below the coverage threshold rather than 0?
* What breaks if a new modality writes `gene_id`/`count` instead of `feature_id`/`value`?
* Plant CHH methylation of 0.3: signal or artifact? Which analyte value decides (Module 3)?

## Evidence to submit

* Your coverage-threshold table and the pytest output.

## Handoff to Module 7

Every number above can be wrong for reasons upstream. Module 7 is QC at every level.
