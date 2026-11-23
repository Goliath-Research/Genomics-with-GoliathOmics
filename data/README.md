# Course Data

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

The course uses exactly one biological sample, all of it public:

* **ENA/SRA run SRR28293403**: whole-genome bisulfite sequencing (Illumina NovaSeq 6000) of the
  HG00621 lymphoblastoid cell line, sample SAMN40381571 ("WGBS-HG00621-Rep1"), GEO GSE261315,
  BioProject PRJNA1086543.
* **HG00621** is a 1000 Genomes Project participant (Han Chinese South); the sex recorded in the
  lab (male) comes from BioSample SAME123082.

ENA publishes these records without access restrictions. No patient, customer or invented data is
used anywhere in the course.

## Files

* `fixtures/SRR28293403_{1,2}.first1000.fastq.gz`: records 1–1000 of each mate file, unmodified,
  re-gzipped. `fixtures/manifest.json` lists source URLs, sha256 and the full run's ENA md5.
* `fetch_public_data.py --verify` checks the fixtures; `--pairs N` streams the first N pairs from
  ENA into `data/downloads/` (git-ignored).
