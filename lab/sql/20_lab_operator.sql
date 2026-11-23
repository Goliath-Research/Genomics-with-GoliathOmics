-- Goliath Research Academy lab: one local operator account and one organization, so the portal
-- and the official semantic write functions have an authenticated actor to record.
--
-- This is lab infrastructure, not tenant or customer data: the organization is the disposable lab
-- itself and the operator is you. Uses GoliathApp's portal.sp_organization_create and
-- portal.sp_organization_set_admin. GoliathApp has no "create user" procedure (identities normally
-- arrive through an identity provider), so the user row is inserted directly.
--
-- Variables (psql -v): operator_name, operator_email. Idempotent on the email.

\set ON_ERROR_STOP on
\if :{?operator_name}
\else
  \set operator_name 'Academy Lab Operator'
\endif
\if :{?operator_email}
\else
  \set operator_email 'operator@academy-lab.invalid'
\endif

BEGIN;

INSERT INTO "RBAC"."Users" ("FullName", email, "Active", username)
SELECT :'operator_name', :'operator_email', 1, 'lab_operator'
WHERE NOT EXISTS (SELECT 1 FROM "RBAC"."Users" WHERE email = :'operator_email');

DO $org$
DECLARE
  v_user int;
  v_org int;
BEGIN
  SELECT "ID" INTO v_user FROM "RBAC"."Users" WHERE username = 'lab_operator' ORDER BY "ID" LIMIT 1;
  SELECT "ID" INTO v_org FROM portal."Organizations" WHERE "Name" = 'Academy Lab (local)';
  IF v_org IS NULL THEN
    SELECT organization_id INTO v_org FROM portal.sp_organization_create('Academy Lab (local)');
  END IF;
  PERFORM portal.sp_organization_set_admin(v_org, v_user);
END
$org$;

COMMIT;

-- Re-grant the baseline operator menu to the new organization scope.
SELECT portal.sp_sync_god_architect_operator_entitlements();
