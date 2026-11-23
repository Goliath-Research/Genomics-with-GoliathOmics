#!/usr/bin/env bash
# Module 9 exercise: run the official GoliathOmics study-start drain once against the lab database.
# It needs no worker and spends nothing. Without a materialized /work project it records a failure
# on the queued request, which is the point of the exercise.
set -euo pipefail
SRC_DIR="${SRC_DIR:-/lab-src}"
APP="$SRC_DIR/GoliathApp"; OMICS="$SRC_DIR/GoliathOmics"
export BACKEND_DB=postgres
export POSTGRES_HOST="${PGHOST:-db}" POSTGRES_PORT="${PGPORT:-5432}" POSTGRES_DB="${LAB_DB:-goliath_omics_lab}"
export POSTGRES_USER="${PGUSER:-postgres}" POSTGRES_PASSWORD="${PGPASSWORD:-}"
export PYTHONPATH="$APP:$APP/workflow_engine:$OMICS/workers:$OMICS/domain/src:$OMICS/src:$OMICS/workflow_engine"
cd "$OMICS"
"${VENV_DIR:-$SRC_DIR/venv}/bin/python" workflow_engine/admin/study_start.py drain-requests --limit 1 || true
