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

  -- History and UTC (GoliathApp #109-#113, GoliathOmics #116-#117): ledgers verify clean and no
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
END
$verify$;

SELECT 'omics classes' AS check, count(*)::text AS value FROM "Meta"."Classes" WHERE "Name" LIKE 'omics/%'
UNION ALL SELECT 'workflow actions', count(*)::text FROM wf.workflow_action
UNION ALL SELECT 'workflow definitions', count(*)::text FROM wf.workflow_def
UNION ALL SELECT 'published analytes', count(*)::text FROM cfg.analyte WHERE status = 'published'
UNION ALL SELECT 'assay procedures', count(*)::text FROM cfg.assay_procedure
UNION ALL SELECT 'public patients', count(*)::text FROM portal."Patients"
UNION ALL SELECT 'public samples', count(*)::text FROM portal."Samples";
