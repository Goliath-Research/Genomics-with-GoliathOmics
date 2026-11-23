-- Module 9: the execution record in the lab database. Read-only queries.
\pset pager off

-- 1. Definitions and versions
SELECT d.name, v.version_major || '.' || v.version_minor AS version, v.is_active
FROM wf.workflow_def d JOIN wf.workflow_version v ON v.workflow_def_id = d.id
ORDER BY d.name, v.version_major, v.version_minor;

-- 2. The queued SamplePrep request for the public sample
SELECT r.id, s.name AS study, r.stage, r.status, r.workflow_version_id, r.workflow_instance_id,
       r.created_by, r.created_at_utc, left(r.error_message, 120) AS error
FROM cfg.study_start_request r JOIN cfg.study s ON s.id = r.study_row_id;

-- 3. Instances and step attempts (empty until a drain succeeds)
SELECT count(*) AS instances FROM wf.workflow_instance;
SELECT count(*) AS node_executions FROM wf.node_execution;

-- 4. Platform audit tables
SELECT 'record_editor_audit' AS audit, count(*) FROM portal.record_editor_audit
UNION ALL SELECT 'model_authoring_audit', count(*) FROM portal.model_authoring_audit
UNION ALL SELECT 'security_admin_audit', count(*) FROM portal.security_admin_audit
UNION ALL SELECT 'session_active_role_audit', count(*) FROM portal.session_active_role_audit
UNION ALL SELECT 'god_architect_audit', count(*) FROM portal.god_architect_audit
UNION ALL SELECT 'external_identity_link_audit', count(*) FROM portal.external_identity_link_audit;

-- 5. Clinical writes and the Meta mirror switch
SELECT entity_code, dual_write_legacy_meta, read_from_meta FROM omics_clinical.meta_cutover_flag ORDER BY 1;

-- 6. Runs and alignments as Meta objects (GoliathOmics #119)
-- 6a. The writers are class methods
SELECT c."Name" AS class, m."Name" AS method, m."ImplKind", m."ImplRef"
FROM "Meta"."Methods" m JOIN "Meta"."Classes" c ON c."ID" = m."ClassID"
WHERE c."Name" IN ('omics/SequencingRun', 'omics/AlignmentResult')
ORDER BY 1, 2;
-- 6b. Which actions produce which class
SELECT action_name, class_name FROM omics_clinical.wf_meta_object_source ORDER BY class_name, action_name;
-- 6c. The engine hook
SELECT tgname, tgenabled FROM pg_trigger
WHERE tgrelid = 'wf.node_execution'::regclass AND tgname = 'trg_omics_node_execution_meta_objects';
-- 6d. Objects vs successful source steps (equal; 0 = 0 in a fresh lab)
SELECT s.class_name,
       count(DISTINCT ne.id) AS source_steps,
       (SELECT count(*) FROM omics_clinical.wf_meta_object_link l WHERE l.class_name = s.class_name) AS objects
FROM omics_clinical.wf_meta_object_source s
LEFT JOIN wf.workflow_action wa ON wa.action_name = s.action_name
LEFT JOIN wf.workflow_node n ON n.workflow_action_id = wa.id
LEFT JOIN wf.node_execution ne ON ne.workflow_node_id = n.id AND ne.status = 'SUCCEEDED'
GROUP BY 1 ORDER BY 1;
SELECT count(*) AS pending FROM omics_clinical.v_run_alignment_pending;
-- 6e. Backfill dry run: what the official backfill would create now (nothing is kept)
BEGIN;
SELECT * FROM omics_clinical.sp_run_alignment_backfill();
ROLLBACK;
