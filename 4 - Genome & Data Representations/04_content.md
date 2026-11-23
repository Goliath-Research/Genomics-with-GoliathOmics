# Module 4: Genome & Data Representations

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

**Notebook:** `04_fastq_and_sam_anatomy.py` · **Support code:** `module_04_formats.py` ·
**Dataset:** `data/fixtures/SRR28293403_{1,2}.first1000.fastq.gz` (public, checksummed) ·
**Sources:** GoliathOmics `docs/architecture/site-parameters.md`,
`schemas/config/site_manifest.schema.json`, `schemas/domain/{fastq_storage,h5_storage,sample_storage}.schema.json`,
`docs/usage/03-sample-prep-and-qc.md` ("Where artifacts live"), `docs/usage/20-…`, `22-…`

## Goal

Read the files every modality produces, know which reference each one is relative to, and know
which formats GoliathOmics actually writes today.

## 4.1 References are coordinate systems

A reference genome is an assembly (GRCh38), a release (for example Ensembl 116) and the indexes
built for one aligner. A **pangenome** is a graph of many haplotypes (HPRC); it reduces reference
bias. An annotation (GTF) places genes and transcripts on the assembly. Proteomics uses a protein
FASTA (UniProt) and optionally a spectral library.

GoliathOmics pins all of these **once per site** in the typed `omics/SiteParameters` document,
never per study:

| Site key | Used by |
|---|---|
| `reference_selection`, `reference_genome.fasta`, `annotation.gtf` | linear WGBS, extraction, annotation |
| `pangenome_genome`, `pangenome_wgbs_genome` | Giraffe and methylGrapher paths |
| `rna_reference` (`star_index_dir`, `gtf`, `kallisto_index`, `tx2gene`, …) | RNA-seq |
| `proteomics_reference` (`protein_fasta`, `spectral_library`, `prosit_model`, `casanovo_model`) | proteomics |

Site examples: `workflow_engine/domain/profiles/site_grch38.example.json`,
`site_tair10.example.json` (Arabidopsis) and the crop sites used by the plant pack.

## 4.2 The file chain per modality

| Modality | Raw | Aligned / searched | Per-sample features | Written by GoliathOmics today |
|---|---|---|---|---|
| Methylation (linear) | FASTQ | BAM (worker scratch) | `{chr}-CG.h5`, optional `{chr}-CG.patterns.h5`, `extraction_manifest.json` | yes |
| Methylation (pangenome) | FASTQ | GAF (graph alignments), surjected BAM | same HDF5 matrices | yes |
| RNA-seq | FASTQ | STAR BAM + gene counts, or kallisto `abundance.tsv` | `{sample_id}.expression.h5` (`gene_id`, `count`, `tpm`) | yes |
| Proteomics | raw spectra, or a panel matrix | DIA-NN report / Sage search | `abundance.h5` | yes |
| Variants | — | CRAM, VCF | — | **no** (concepts only) |

CRAM output and variant calling are not GoliathOmics features today. They appear in this module
as ecosystem formats so you can recognize them, not as platform outputs.

## 4.3 FASTQ

Four lines per read: `@name`, sequence, `+`, qualities (Phred+33: `F` = 37, `:` = 25,
`,` = 11, `#` = 2). The course fixture is the first 1,000 read pairs of SRR28293403, 151 bp each.
Expected values from the notebook:

| Mate | C | G | %Q30 | Reads with TruSeq adapter |
|---|---|---|---|---|
| R1 | 4.8% | 21.9% | 87.5 | 32.3% |
| R2 | 18.7% | 8.9% | 90.9 | 33.7% |

R1 has almost no C: unmethylated C was read as T. R2 reads the complementary strand, so its G is
depleted. That signature is the first thing to check on any bisulfite or EM-Seq run.

## 4.4 SAM/BAM

One line per alignment: `QNAME FLAG RNAME POS MAPQ CIGAR RNEXT PNEXT TLEN SEQ QUAL [tags]`.

* **FLAG** is a bit field. `99` = paired, proper pair, mate reverse, first in pair; `147` = its
  mate (paired, proper pair, reverse, second in pair).
* **MAPQ** is the aligner's confidence that the position is right.
* **CIGAR** describes the alignment: `5S60M2I30M1D54M` spans 145 reference bases and uses all 151
  read bases.
* Bisulfite aligners add their own tags. Bismark, for example, writes `XM` (per-base methylation
  call string), `XR` (read conversion) and `XG` (which converted genome the read aligned to);
  bwa-meth-style aligners record the converted strand differently. Extraction (Module 6) reads
  these alignments, not the tags, to call methylation.

BAMs live only in worker scratch in GoliathOmics; the durable hand-off is the HDF5 matrix plus
the QC JSON and manifests (Module 6, Module 9).

## Lab sequence

1. `python data/fetch_public_data.py --verify` (both fixtures `ok`).
2. `marimo edit "4 - Genome & Data Representations/04_fastq_and_sam_anatomy.py"`: check the table
   above, find the lowest-quality cycles, decode flags 83, 99, 147, 163, 4 and 256.
3. Optional, larger subset: `python data/fetch_public_data.py --pairs 100000` streams 100,000
   pairs from ENA into `data/downloads/` (never committed).

## Practice

* Why does R1 lose C while R2 loses G? Draw both strands for one CpG.
* What would the composition table look like for an RNA-seq FASTQ? For EM-Seq?
* A study needs CRAM for long-term storage. Is that a platform feature today? Where would it be
  configured if added? (No; a new action plus a site/storage setting.)

## Evidence to submit

* The completed composition table from your notebook run, with the five lowest cycles.
* Your decoded flags.

## Handoff to Module 5

These reads cannot be aligned like ordinary DNA. Module 5 shows how each modality maps or searches
its raw data, and how GoliathOmics chooses the path.
