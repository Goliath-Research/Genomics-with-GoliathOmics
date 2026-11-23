#!/usr/bin/env bash
# Populate the course lab database with the official GoliathApp + GoliathOmics apply and seed
# scripts, then load the one public ENA sample (SRR28293403 / HG00621).
#
# Runs inside the `seed` Compose service (see compose.yaml) or natively for CI and development.
# It never connects anywhere except the database named by the PG* variables, and it refuses to
# run against a host that is not local unless GOLIATH_LAB_ALLOW_REMOTE=1 (never point it at Neon
# or production).
#
# Inputs (environment):
#   PGHOST PGPORT PGUSER PGPASSWORD   admin connection to the lab server (libpq names)
#   LAB_DB                            database to create/populate (default goliath_omics_lab)
#   SRC_DIR                           where GoliathApp/ and GoliathOmics/ checkouts live
#   GOLIATH_APP_REF / GOLIATH_OMICS_REF   commits to check out (default: lab/pins.env)
#   VENV_DIR                          Python venv for the seed scripts (default $SRC_DIR/venv)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
set -a; source "$HERE/pins.env"; set +a
GOLIATH_APP_REF="${GOLIATH_APP_REF_OVERRIDE:-$GOLIATH_APP_REF}"
GOLIATH_OMICS_REF="${GOLIATH_OMICS_REF_OVERRIDE:-$GOLIATH_OMICS_REF}"

LAB_DB="${LAB_DB:-goliath_omics_lab}"
SRC_DIR="${SRC_DIR:-$HERE/../.lab-src}"
VENV_DIR="${VENV_DIR:-$SRC_DIR/venv}"
export PGHOST="${PGHOST:-127.0.0.1}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-postgres}"
export PGSSLMODE="${PGSSLMODE:-disable}"

log() { printf '[lab %s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

case "$PGHOST" in
  127.0.0.1|localhost|db|::1) ;;
  *) [[ "${GOLIATH_LAB_ALLOW_REMOTE:-0}" == "1" ]] || {
       echo "Refusing to seed non-local host '$PGHOST' (set GOLIATH_LAB_ALLOW_REMOTE=1 only for another disposable server)." >&2
       exit 2; } ;;
esac

for tool in git jq psql python3; do
  command -v "$tool" >/dev/null 2>&1 || { echo "$tool is required" >&2; exit 1; }
done

psql_admin() { PGDATABASE=postgres psql -X -q -v ON_ERROR_STOP=1 "$@"; }
psql_lab() { PGDATABASE="$LAB_DB" psql -X -q -v ON_ERROR_STOP=1 "$@"; }

log "waiting for PostgreSQL at $PGHOST:$PGPORT"
for _ in $(seq 1 60); do
  psql_admin -t -A -c 'SELECT 1' >/dev/null 2>&1 && break
  sleep 2
done
SERVER_MAJOR="$(psql_admin -t -A -c 'SHOW server_version_num' | cut -c1-2)"
log "server major version $SERVER_MAJOR"
if (( SERVER_MAJOR < 18 || SERVER_MAJOR >= 20 )); then
  echo "PostgreSQL 18 or 19 required (Academy standard is 19)" >&2
  exit 1
fi

checkout() {
  local name="$1" ref="$2" dir="$SRC_DIR/$1"
  if [[ ! -d "$dir/.git" ]]; then
    log "cloning $name"
    git clone -q "https://github.com/Goliath-Research/$name.git" "$dir"
  fi
  if ! git -C "$dir" cat-file -e "$ref^{commit}" 2>/dev/null; then
    git -C "$dir" fetch -q origin "$ref" || git -C "$dir" fetch -q origin
  fi
  git -C "$dir" checkout -q --detach "$ref"
  log "$name at $(git -C "$dir" rev-parse --short HEAD)"
}
mkdir -p "$SRC_DIR"
checkout GoliathApp "$GOLIATH_APP_REF"
checkout GoliathOmics "$GOLIATH_OMICS_REF"
APP="$SRC_DIR/GoliathApp"
OMICS="$SRC_DIR/GoliathOmics"

if [[ "$(psql_admin -t -A -c "SELECT count(*) FROM pg_database WHERE datname = '$LAB_DB'")" == "0" ]]; then
  log "creating database $LAB_DB"
  psql_admin -c "CREATE DATABASE \"$LAB_DB\""
fi
export PGDATABASE="$LAB_DB"

log "bundling GoliathApp and GoliathOmics SQL (release-shaped, as the official smoke does)"
REL="$SRC_DIR/release"
rm -rf "$REL" && mkdir -p "$REL"
printf '{"version":"academy-lab"}\n' >"$REL/manifest.json"
python3 "$OMICS/scripts/bundle_goliathapp_sql.py" --sql-dir "$APP/workflow_engine/sql_pg" \
  --out "$REL/goliathapp-sql" --commit "$(git -C "$APP" rev-parse HEAD)" >/dev/null
python3 "$OMICS/scripts/bundle_omics_sql.py" --sql-dir "$OMICS/workflow_engine/sql_pg" \
  --out "$REL/omics-sql" --commit "$(git -C "$OMICS" rev-parse HEAD)" >/dev/null

log "apply_goliathapp_schema.sh"
bash "$OMICS/scripts/apply_goliathapp_schema.sh" --release-dir "$REL" >"$SRC_DIR/apply_goliathapp.log" 2>&1 \
  || { tail -40 "$SRC_DIR/apply_goliathapp.log" >&2; exit 1; }
log "apply_omics_schema.sh"
bash "$OMICS/scripts/apply_omics_schema.sh" --release-dir "$REL" >"$SRC_DIR/apply_omics.log" 2>&1 \
  || { tail -40 "$SRC_DIR/apply_omics.log" >&2; exit 1; }

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  log "creating seed venv"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q -U pip
fi
log "installing seed packages (same set as GoliathOmics smoke_populate_disposable_db.sh)"
pipq() { "$VENV_DIR/bin/pip" install -q "$@" >>"$SRC_DIR/pip.log" 2>&1; }
pipq "psycopg[binary]>=3.1" pydantic psutil
for pkg in methylutils methyldomain methyldetector methylmapper methylenricher methyldiseaseprogression methylclassifier; do
  pipq -e "$OMICS/packages/$pkg"
done
pipq -e "$APP/workflow_engine"
pipq -e "$OMICS/domain" --no-deps
pipq -e "$OMICS/docs/examples/python"

export PYTHONPATH="$APP:$APP/workflow_engine:$OMICS/workers:$OMICS/domain/src:$OMICS/src${PYTHONPATH:+:$PYTHONPATH}"
PY="$VENV_DIR/bin/python"
BIN="$VENV_DIR/bin"

log "GoliathApp platform seeds: semantic catalog, action catalog, baseline NavTree"
"$PY" "$APP/workflow_engine/sql_pg/seed_semantic_catalog.py" >"$SRC_DIR/seed_semantic_app.log" 2>&1 \
  || { tail -30 "$SRC_DIR/seed_semantic_app.log" >&2; exit 1; }
"$PY" "$APP/workflow_engine/sql_pg/seed_action_catalog.py" --use-db >"$SRC_DIR/seed_actions_app.log" 2>&1 \
  || { tail -30 "$SRC_DIR/seed_actions_app.log" >&2; exit 1; }
psql_lab -f "$APP/workflow_engine/sql_pg/seed_platform_nav_tree.sql" >/dev/null

log "GoliathOmics cfg documents (analytes, profiles, procedures)"
"$PY" "$OMICS/scripts/sync_cfg_profiles_and_action_catalog.py" --backend postgres --skip-seed \
  >"$SRC_DIR/sync_cfg.log" 2>&1 || { tail -30 "$SRC_DIR/sync_cfg.log" >&2; exit 1; }
log "GoliathOmics action catalog"
"$PY" "$OMICS/workflow_engine/sql_pg/seed_action_catalog.py" --use-db >"$SRC_DIR/seed_actions_omics.log" 2>&1 \
  || { tail -30 "$SRC_DIR/seed_actions_omics.log" >&2; exit 1; }

log "GoliathOmics DomainPrograms"
export BACKEND_DB=postgres POSTGRES_HOST="$PGHOST" POSTGRES_PORT="$PGPORT" POSTGRES_DB="$LAB_DB" POSTGRES_USER="$PGUSER"
export POSTGRES_PASSWORD="${PGPASSWORD:-}"
export GOLIATH_APP_ROOT="$APP" GOLIATH_ENV_DIR="$SRC_DIR/goliath-env" PYTHON_BIN="$PY"
bash "$OMICS/scripts/deploy_workflow_definitions.sh" >"$SRC_DIR/deploy_workflows.log" 2>&1 \
  || { tail -30 "$SRC_DIR/deploy_workflows.log" >&2; exit 1; }

log "GoliathOmics Meta classes, semantic catalog, NavTree, config document types, action methods"
for seed in goliath-omics-seed-meta-classes goliath-omics-seed-semantic goliath-omics-seed-nav \
            goliath-omics-seed-config-document-types goliath-omics-seed-meta-action-methods; do
  "$BIN/$seed" >"$SRC_DIR/$seed.log" 2>&1 || { echo "$seed failed:" >&2; tail -30 "$SRC_DIR/$seed.log" >&2; exit 1; }
done

log "public ENA study + SamplePrep queue row (official enqueue SQL)"
psql_lab -f "$HERE/sql/10_academy_ena_canary_study.sql" >/dev/null
STUDY_ROW_ID="$(psql_lab -t -A -c "SELECT id FROM cfg.study WHERE name = 'academy_ena_srr28293403' AND version = '1'")"
if [[ "$(psql_lab -t -A -c "SELECT count(*) FROM cfg.study_start_request WHERE study_row_id = $STUDY_ROW_ID")" == "0" ]]; then
  psql_lab \
    -v "study_row_id=$STUDY_ROW_ID" \
    -v "workflow_version_id=0" \
    -v "project_path=/work/projects/academy_ena_srr28293403/configs/project_academy_ena_srr28293403.json" \
    -v "samples_json=[{\"sampleId\":\"canary-SRR28293403-linear-subset\",\"fastqPrefix\":\"SRR28293403/\"}]" \
    -v "fastq_storage_json={\"type\":\"file\",\"basePath\":\"/work/genomes/pangenome/canary/gse261315/SRR28293403/subset\"}" \
    -f "$OMICS/workflow_engine/sql_pg/enqueue_sample_prep_test_start.sql" >/dev/null
fi

log "lab operator account and organization"
psql_lab -v "operator_name=${LAB_OPERATOR_NAME:-Academy Lab Operator}" -v "operator_email=${LAB_OPERATOR_EMAIL:-operator@academy-lab.invalid}" \
  -f "$HERE/sql/20_lab_operator.sql" >/dev/null
# The lab organization did not exist when the nav seeds first ran. Both files are official and
# idempotent; GoliathApp documents re-running its nav seed after creating an organization, and
# GoliathOmics registers /app/omics only once the platform /app root exists
# (docs/architecture/database-population.md, "Shared platform host").
log "re-running official NavTree seeds for the lab organization scope"
psql_lab -f "$APP/workflow_engine/sql_pg/seed_platform_nav_tree.sql" >/dev/null
psql_lab -f "$OMICS/database/schema/16_omics_portal_host_nav.sql" >/dev/null 2>&1

log "public ENA rows: Institution ENA, Patient HG00621, Sample (import_ena_public_samples.py --apply)"
"$PY" "$OMICS/scripts/import_ena_public_samples.py" --apply >"$SRC_DIR/import_ena.log" 2>&1 \
  || { tail -30 "$SRC_DIR/import_ena.log" >&2; exit 1; }
for entity in institution patient sample; do
  bash "$OMICS/scripts/omics_meta_backfill.sh" "$entity" >>"$SRC_DIR/backfill.log" 2>&1 \
    || { tail -30 "$SRC_DIR/backfill.log" >&2; exit 1; }
done

if [[ -n "${GOLIATH_PORTAL_DB_PASSWORD:-}" ]]; then
  # Official GoliathOmics script; sets the goliath_portal login password so the local portal can
  # connect. The password comes from your local .env and never leaves the lab. The script insists
  # on PGPASSWORD; a trust-auth native cluster ignores the placeholder.
  log "apply_gateway_db_roles.sh (goliath_portal login for the local portal)"
  PGDATABASE="$LAB_DB" PGPASSWORD="${PGPASSWORD:-trust-auth-placeholder}" GOLIATH_GATEWAY_DB_PASSWORD="" \
    bash "$OMICS/scripts/apply_gateway_db_roles.sh" >"$SRC_DIR/gateway_roles.log" 2>&1 \
    || { tail -20 "$SRC_DIR/gateway_roles.log" >&2; exit 1; }
fi

log "verifying"
psql_lab -f "$OMICS/docs/examples/sql/verify_schema_ledgers.sql" >/dev/null
psql_lab -f "$OMICS/docs/examples/sql/verify_population_invariants.sql" >/dev/null
psql_lab -f "$HERE/sql/90_verify_lab.sql"
log "lab database $LAB_DB is ready"
