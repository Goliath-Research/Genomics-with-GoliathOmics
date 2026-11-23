-- Fail loudly if the lab database is not in the state the course modules expect.
\set ON_ERROR_STOP on
DO $verify$
DECLARE
  n int;
BEGIN
  SELECT count(*) INTO n FROM "Meta"."Classes" WHERE "Name" LIKE 'omics/%';
  IF n < 11 THEN RAISE EXCEPTION 'expected at least 11 omics/* Meta classes, found %', n; END IF;

  SELECT count(*) INTO n FROM wf.workflow_action;
  IF n < 50 THEN RAISE EXCEPTION 'expected the GoliathApp + GoliathOmics action catalog, found % actions', n; END IF;

  SELECT count(*) INTO n
  FROM wf.workflow_version v JOIN wf.workflow_def d ON d.id = v.workflow_def_id
  WHERE d.name = 'SamplePrepPipeline' AND v.is_active;
  IF n < 1 THEN RAISE EXCEPTION 'no active SamplePrepPipeline version'; END IF;

  SELECT count(*) INTO n FROM portal."Institutions" WHERE "Name" = 'ENA';
  IF n <> 1 THEN RAISE EXCEPTION 'expected Institution ENA, found %', n; END IF;

  SELECT count(*) INTO n
  FROM portal."Patients" p JOIN portal."Institutions" i ON i."ID" = p."InstitutionID"
  WHERE p."ExternalID" = 'HG00621' AND i."Name" = 'ENA'
    AND p."Race" IS NULL AND p."Ethnicity" IS NULL AND p."YearBorn" IS NULL;
  IF n <> 1 THEN RAISE EXCEPTION 'expected public donor HG00621 with no invented demographics, found %', n; END IF;

  SELECT count(*) INTO n FROM portal."Samples" WHERE "SampleName" = 'canary-SRR28293403-linear-subset' AND "CustomerID" IS NULL;
  IF n <> 1 THEN RAISE EXCEPTION 'expected public sample canary-SRR28293403-linear-subset, found %', n; END IF;

  -- Only public data: every patient and sample in the lab comes from the ENA import.
  SELECT count(*) INTO n FROM portal."Patients" WHERE "ExternalID" IS DISTINCT FROM 'HG00621';
  IF n <> 0 THEN RAISE EXCEPTION 'lab must hold only the public donor HG00621; found % other patients', n; END IF;
  SELECT count(*) INTO n FROM portal."Customers";
  IF n <> 0 THEN RAISE EXCEPTION 'lab must hold no customers; found %', n; END IF;

  -- Portal reachability: organization admins hold the omics request permissions and the
  -- /app/omics NavTree branch in the lab organization scope.
  SELECT count(*) INTO n
  FROM "RBAC"."Role_Permissions" rp
  JOIN "RBAC"."Roles" r ON r."ID" = rp."RoleID"
  JOIN "RBAC"."Permissions" p ON p."ID" = rp."PermissionID"
  WHERE r."Name" = 'organization_admin' AND p."Name" IN ('omics.clinical.read', 'omics.clinical.write');
  IF n <> 2 THEN RAISE EXCEPTION 'organization_admin lacks omics.clinical.read/write (needs GoliathOmics #115)'; END IF;

  SELECT count(*) INTO n
  FROM portal."Role2Node" rn
  JOIN portal."NavTree" t ON t."ID" = rn."NodeId"
  JOIN "RBAC"."Roles" r ON r."ID" = rn."RoleId"
  WHERE r."Name" = 'organization_admin' AND t."NodePath" = '/app/omics/patients';
  IF n < 1 THEN RAISE EXCEPTION 'organization_admin has no /app/omics/patients nav grant'; END IF;

  -- History and UTC (GoliathApp #109-#113, GoliathOmics #116-#118): ledgers verify clean and no
  -- timestamp default or function stores a UTC wall clock. Skipped on an older pin.
  IF to_regprocedure('portal.fn_ledger_verify_all()') IS NOT NULL THEN
    EXECUTE 'SELECT count(*) FROM portal.fn_ledger_verify_all()' INTO n;
    IF n <> 0 THEN RAISE EXCEPTION 'portal.fn_ledger_verify_all() reports % problem(s)', n; END IF;
  END IF;
  IF to_regprocedure('portal.fn_utc_timestamp_violations()') IS NOT NULL THEN
    EXECUTE 'SELECT count(*) FROM portal.fn_utc_timestamp_violations()' INTO n;
    IF n <> 0 THEN RAISE EXCEPTION 'portal.fn_utc_timestamp_violations() lists % object(s)', n; END IF;
  END IF;
  IF to_regprocedure('omics_clinical.fn_utc_timestamp_violations()') IS NOT NULL THEN
    EXECUTE 'SELECT count(*) FROM omics_clinical.fn_utc_timestamp_violations()' INTO n;
    IF n <> 0 THEN RAISE EXCEPTION 'omics_clinical.fn_utc_timestamp_violations() lists % object(s)', n; END IF;
  END IF;
  -- Runs and alignments (GoliathOmics #119): the writers are class methods, the engine hook is
  -- enabled, and every successful source step has exactly one object (0 = 0 in a fresh lab).
  SELECT count(*) INTO n
  FROM "Meta"."Methods" m JOIN "Meta"."Classes" c ON c."ID" = m."ClassID"
  WHERE (c."Name", m."Name", m."ImplRef") IN (
    ('omics/SequencingRun', 'RecordFromNodeExecution', 'omics_clinical.sp_sequencing_run_record'),
    ('omics/AlignmentResult', 'RecordFromNodeExecution', 'omics_clinical.sp_alignment_result_record'),
    ('omics/SequencingRun', 'Backfill', 'omics_clinical.sp_run_alignment_backfill'),
    ('omics/AlignmentResult', 'Backfill', 'omics_clinical.sp_run_alignment_backfill'));
  IF n <> 4 THEN RAISE EXCEPTION 'expected 4 run/alignment writer methods, found % (needs GoliathOmics #119)', n; END IF;
  SELECT count(*) INTO n FROM pg_trigger
  WHERE tgrelid = 'wf.node_execution'::regclass AND tgname = 'trg_omics_node_execution_meta_objects' AND tgenabled = 'O';
  IF n <> 1 THEN RAISE EXCEPTION 'run/alignment engine hook missing or disabled'; END IF;
  SELECT count(*) INTO n FROM omics_clinical.v_run_alignment_pending;
  IF n <> 0 THEN RAISE EXCEPTION '% successful step(s) have no run/alignment object; run the backfill', n; END IF;
  SELECT count(*) INTO n
  FROM omics_clinical.wf_meta_object_link l
  LEFT JOIN "Meta"."Objs" o ON o."ID" = l.meta_obj_id
  LEFT JOIN "Meta"."Classes" c ON c."ID" = o."ClassID"
  WHERE c."Name" IS DISTINCT FROM l.class_name;
  IF n <> 0 THEN RAISE EXCEPTION '% run/alignment link(s) point at a missing or wrong-class object', n; END IF;

  -- Every timestamp column is an absolute instant (timestamptz), including the release ledgers.
  SELECT count(*) INTO n
  FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace ns ON ns.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped
    AND a.atttypid = 'timestamp'::regtype
    AND ns.nspname NOT IN ('pg_catalog', 'information_schema') AND ns.nspname NOT LIKE 'pg_toast%';
  IF n <> 0 THEN RAISE EXCEPTION '% timestamp column(s) without time zone remain', n; END IF;
END
$verify$;

SELECT 'omics classes' AS check, count(*)::text AS value FROM "Meta"."Classes" WHERE "Name" LIKE 'omics/%'
UNION ALL SELECT 'workflow actions', count(*)::text FROM wf.workflow_action
UNION ALL SELECT 'workflow definitions', count(*)::text FROM wf.workflow_def
UNION ALL SELECT 'published analytes', count(*)::text FROM cfg.analyte WHERE status = 'published'
UNION ALL SELECT 'assay procedures', count(*)::text FROM cfg.assay_procedure
UNION ALL SELECT 'public patients', count(*)::text FROM portal."Patients"
UNION ALL SELECT 'public samples', count(*)::text FROM portal."Samples"
UNION ALL SELECT 'sequencing runs', count(*)::text FROM omics_clinical.wf_meta_object_link WHERE class_name = 'omics/SequencingRun'
UNION ALL SELECT 'alignment results', count(*)::text FROM omics_clinical.wf_meta_object_link WHERE class_name = 'omics/AlignmentResult';
