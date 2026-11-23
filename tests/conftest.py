"""Shared helpers for the course tests.

Offline tests need nothing but the repo. Drift tests compare the course's teaching copies with the
pinned GoliathOmics checkout in ``.lab-src/GoliathOmics`` (or ``$GOLIATH_LAB_SRC``) and skip when
it is absent. Live tests (``-m live``) need a running lab: ``GOLIATH_LAB_DSN`` for the database and
``GOLIATH_PORTAL_URL`` + ``GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET`` for the portal.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = Path(os.environ.get("GOLIATH_LAB_SRC", ROOT / ".lab-src"))
OMICS_SRC = LAB_SRC / "GoliathOmics"


def module_dirs() -> list[Path]:
    dirs = [p for p in ROOT.iterdir() if p.is_dir() and p.name.split(" - ")[0].isdigit()]
    return sorted(dirs, key=lambda p: int(p.name.split(" - ")[0]))


def load_module(number: int, filename: str):
    folder = next(d for d in module_dirs() if d.name.startswith(f"{number} - "))
    path = folder / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def omics_src() -> Path:
    if not (OMICS_SRC / "schemas").is_dir():
        pytest.skip("pinned GoliathOmics checkout not present (.lab-src/GoliathOmics or $GOLIATH_LAB_SRC)")
    return OMICS_SRC


def load_official(src: Path, relative: str):
    """Load one GoliathOmics source file by path, without importing its (heavy) package."""
    path = src / relative
    name = "official_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
