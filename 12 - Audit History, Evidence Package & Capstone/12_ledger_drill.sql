-- Module 12 lab: the history ledger drill (GoliathApp History H1).
--
-- Runs against the course lab database:  python course_lab.py sql "12 - Audit History, Evidence Package & Capstone/12_ledger_drill.sql"
-- Everything happens inside one transaction that is ROLLED BACK at the end, so the lab's
-- real history is unchanged. Requires GoliathApp with History H1 (portal.fn_ledger_verify_all);
-- on an older pin the script says so and does nothing.
\set ON_ERROR_STOP on
SET TimeZone = 'UTC';
BEGIN;

DO $drill$
DECLARE
  v_session int;
  v_user int;
  v_scope int;
  v_role int;
  v_seq bigint;
  v_problems int;
  r record;
BEGIN
  IF to_regprocedure('portal.fn_ledger_verify_all()') IS NULL THEN
    RAISE NOTICE 'SKIP: this GoliathApp pin has no History H1 ledger (GoliathApp PR #109). See lab/pins.env.';
    RETURN;
  END IF;

  RAISE NOTICE '1. registered ledgers and their heads (the checkpoint you would export and sign):';
  FOR r IN SELECT * FROM portal.fn_ledger_checkpoint() ORDER BY 1 LOOP
    RAISE NOTICE '   % last_seq=% head=%', r.ledger_name, r.last_seq, coalesce(left(r.last_hash_hex, 16), '-');
  END LOOP;

  SELECT count(*) INTO v_problems FROM portal.fn_ledger_verify_all();
  RAISE NOTICE '2. verify_all before the drill: % problem(s)', v_problems;

  -- A real session if the portal smoke test signed in; otherwise session 0 (rolled back anyway).
  SELECT s."ID", s."UserID", s."ActiveScopeID" INTO v_session, v_user, v_scope
  FROM "RBAC"."Sessions" s ORDER BY s."ID" DESC LIMIT 1;
  IF v_session IS NULL THEN
    SELECT u."ID" INTO v_user FROM "RBAC"."Users" u ORDER BY u."ID" LIMIT 1;
    v_session := 0;
  END IF;
  SELECT "ID" INTO v_role FROM "RBAC"."Roles" WHERE "Name" = 'organization_admin';

  PERFORM portal.fn_session_audit_active_role(v_session, v_user, v_scope, NULL, v_role, 'lab_drill');
  SELECT max(ledger_seq) INTO v_seq FROM portal.session_active_role_audit;
  RAISE NOTICE '3. appended one audit row through the official function: ledger_seq=%', v_seq;

  BEGIN
    UPDATE portal.session_active_role_audit SET action = 'edited' WHERE ledger_seq = v_seq;
    RAISE EXCEPTION 'UNEXPECTED: update was allowed';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM LIKE 'UNEXPECTED%' THEN RAISE; END IF;
    RAISE NOTICE '4. UPDATE rejected: %', SQLERRM;
  END;

  BEGIN
    DELETE FROM portal.session_active_role_audit WHERE ledger_seq = v_seq;
    RAISE EXCEPTION 'UNEXPECTED: delete was allowed';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM LIKE 'UNEXPECTED%' THEN RAISE; END IF;
    RAISE NOTICE '5. DELETE rejected: %', SQLERRM;
  END;

  -- A database owner can still switch the guard off. The chain makes that visible.
  EXECUTE 'ALTER TABLE portal.session_active_role_audit DISABLE TRIGGER trg_ledger_guard';
  UPDATE portal.session_active_role_audit SET action = 'edited_by_owner' WHERE ledger_seq = v_seq;
  EXECUTE 'ALTER TABLE portal.session_active_role_audit ENABLE TRIGGER trg_ledger_guard';
  RAISE NOTICE '6. owner disabled the guard and edited the row; verify_all now reports:';
  FOR r IN SELECT * FROM portal.fn_ledger_verify_all() LOOP
    RAISE NOTICE '   % seq=% %', r.ledger_name, r.ledger_seq, r.problem;
  END LOOP;
  SELECT count(*) INTO v_problems FROM portal.fn_ledger_verify_all();
  IF v_problems = 0 THEN
    RAISE EXCEPTION 'UNEXPECTED: tampering was not detected';
  END IF;
  RAISE NOTICE '7. tamper-evident, not tamper-proof: keep exported checkpoints outside the database.';
END;
$drill$;

ROLLBACK;
