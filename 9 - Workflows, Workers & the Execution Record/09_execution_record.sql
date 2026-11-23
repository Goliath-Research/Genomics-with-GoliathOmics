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

-- 6. Registered but unpopulated classes
SELECT c."Name", count(o."ID") AS objects
FROM "Meta"."Classes" c LEFT JOIN "Meta"."Objs" o ON o."ClassID" = c."ID"
WHERE c."Name" IN ('omics/SequencingRun', 'omics/AlignmentResult')
GROUP BY 1 ORDER BY 1;
