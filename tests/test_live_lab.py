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
