-- Goliath Research Academy lab: one published site and one study that reference the public
-- ENA run SRR28293403 (WGBS of 1000 Genomes donor HG00621, GEO GSE261315).
--
-- Uses only the GoliathApp repository API (cfg.cfg_repo_upsert), the same call as GoliathOmics
-- docs/examples/sql/minimal_study_for_sample_prep_enqueue.sql. No clinical, customer or patient
-- facts are written here: those rows come from GoliathOmics scripts/import_ena_public_samples.py,
-- which records a public source URL for every field.
--
-- The procedure buffy_wgbs_linear_gene_fc only selects the linear WGBS alignment path that the
-- platform canary uses. The sample is a lymphoblastoid cell line, not buffy coat, so the study
-- records primaryAnalyte 'combined' (analyte not asserted) and says so in its description.
--
-- Idempotent: cfg.cfg_repo_upsert is keyed by (name, version).

\set ON_ERROR_STOP on

BEGIN;

SELECT id FROM cfg.cfg_repo_upsert(
  'site',
  'academy_lab_site',
  '1',
  'published',
  jsonb_build_object(
    'catalog', jsonb_build_object(
      'title', 'Academy lab site (local, disposable)',
      'visibility', 'operator',
      'lifecycle', 'active'
    ),
    'displayName', 'Academy lab site'
  )
);

SELECT id FROM cfg.cfg_repo_upsert(
  'study',
  'academy_ena_srr28293403',
  '1',
  'published',
  jsonb_build_object(
    'description', 'Public ENA run SRR28293403 (WGBS-HG00621-Rep1, GSE261315 / PRJNA1086543). '
                   'Linear WGBS path only; analyte not asserted (lymphoblastoid cell line).',
    'pipelineProfile', 'samd_research',
    'pipelineProcedure', 'buffy_wgbs_linear_gene_fc',
    'researchMode', 'gene_fc',
    'primaryAnalyte', 'combined',
    'sample_ids', jsonb_build_array('canary-SRR28293403-linear-subset'),
    'publicSources', jsonb_build_object(
      'runAccession', 'SRR28293403',
      'enaStudy', 'PRJNA1086543',
      'geoSeries', 'GSE261315',
      'filereport', 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=SRR28293403&result=read_run&format=json'
    ),
    'storage', jsonb_build_object(
      'fastqSourceEndpointId', NULL,
      'sampleDestinationEndpointId', NULL
    )
  ),
  NULL::jsonb,
  NULL,
  NULL,
  NULL,
  'academy-ena-SRR28293403'
);

COMMIT;
