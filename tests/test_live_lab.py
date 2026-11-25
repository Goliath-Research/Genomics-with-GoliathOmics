"""Live checks against a running course lab (``pytest -m live``)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT, module_dirs

pytestmark = pytest.mark.live


def _dsn() -> str:
    dsn = os.environ.get("GOLIATH_LAB_DSN")
    if not dsn:
        pytest.skip("GOLIATH_LAB_DSN not set")
    return dsn


def _psql_file(path) -> subprocess.CompletedProcess:
    dsn = _dsn()
    if shutil.which("psql"):
        cmd = ["psql", dsn, "-X", "-v", "ON_ERROR_STOP=1", "-f", str(path)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    # No local client: use the one inside the lab's database container.
    cmd = ["docker", "compose", "exec", "-T", "db", "psql", "-X", "-v", "ON_ERROR_STOP=1",
           "-U", "postgres", "-d", "goliath_omics_lab"]
    with open(path) as sql:
        return subprocess.run(cmd, cwd=ROOT, stdin=sql, capture_output=True, text=True, timeout=300)


def test_lab_verification_sql():
    res = _psql_file(ROOT / "lab" / "sql" / "90_verify_lab.sql")
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_module_9_execution_record_sql():
    folder = next(d for d in module_dirs() if d.name.startswith("9 - "))
    res = _psql_file(folder / "09_execution_record.sql")
    assert res.returncode == 0, res.stderr[-3000:]


def test_module_12_ledger_drill():
    folder = next(d for d in module_dirs() if d.name.startswith("12 - "))
    res = _psql_file(folder / "12_ledger_drill.sql")
    assert res.returncode == 0, res.stderr[-3000:]
    assert "SKIP:" in res.stderr or "hash_mismatch" in res.stderr


def test_public_ena_rows_present():
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_dsn()) as conn:
        row = conn.execute(
            "SELECT count(*) FROM portal.\"Patients\" WHERE \"ExternalID\" = 'HG00621'"
        ).fetchone()
    assert row[0] == 1


def test_portal_smoke():
    if not os.environ.get("GOLIATH_PORTAL_URL"):
        pytest.skip("GOLIATH_PORTAL_URL not set")
    res = subprocess.run([sys.executable, str(ROOT / "lab" / "portal_smoke.py")], capture_output=True, text=True, timeout=600)
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_run_alignment_backfill_is_a_noop_in_the_lab():
    """The official backfill derives objects only from real successful steps: a second pass
    creates and updates nothing, and objects equal source steps."""
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            "SELECT class_name, source_rows, created, updated FROM omics_clinical.sp_run_alignment_backfill()"
        ).fetchall()
        assert {r[0] for r in rows} == {"omics/SequencingRun", "omics/AlignmentResult"}
        assert all(r[2] == 0 and r[3] == 0 for r in rows), rows
        for cls, source_rows, _, _ in rows:
            objs = conn.execute(
                "SELECT count(*) FROM omics_clinical.wf_meta_object_link WHERE class_name = %s", (cls,)
            ).fetchone()[0]
            assert objs == source_rows, (cls, objs, source_rows)
        conn.rollback()
