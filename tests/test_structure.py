"""Repository layout follows the Academy course format."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest

from conftest import ROOT, module_dirs

NOTEBOOKS = sorted(ROOT.glob("[0-9]* - */[0-9][0-9]_*.py"))


def test_twelve_modules_numbered_without_gaps():
    numbers = [int(d.name.split(" - ")[0]) for d in module_dirs()]
    assert numbers == list(range(1, 13))


@pytest.mark.parametrize("folder", module_dirs(), ids=lambda d: d.name)
def test_module_has_content_guide(folder: Path):
    n = int(folder.name.split(" - ")[0])
    guide = folder / f"{n:02d}_content.md"
    assert guide.is_file()
    text = guide.read_text()
    assert text.startswith(f"# Module {n}: ")
    assert "Goliath Research Academy" in text.splitlines()[2]
    assert "](../README.md)" in text
    assert "## Goal" in text and "## Evidence to submit" in text


def test_readme_links_resolve():
    text = (ROOT / "README.md").read_text()
    links = re.findall(r"\]\(([^)#]+?)\)", text)
    local = [unquote(l) for l in links if not l.startswith(("http://", "https://"))]
    assert len(local) >= 14
    for link in local:
        assert (ROOT / link).exists(), link


def test_readme_lists_every_module():
    text = (ROOT / "README.md").read_text()
    for folder in module_dirs():
        assert folder.name in unquote(text), folder.name


def test_no_501k_typo_and_no_compliance_claim():
    for path in ROOT.rglob("*.md"):
        if ".lab-src" in path.parts:
            continue
        text = path.read_text()
        assert "501(k)" not in text.replace('"501(k)"', ""), path
        lowered = text.lower()
        for claim in ("goliathomics is fda-cleared", "goliathomics is part 11 compliant"):
            assert claim not in lowered, path


def test_compose_uses_postgres_19_on_loopback():
    text = (ROOT / "compose.yaml").read_text()
    assert "image: postgres:19-bookworm" in text
    for port in re.findall(r'- "([^"]+)"', text):
        assert port.startswith("127.0.0.1:"), port
    assert "FROM postgres:19-bookworm" in (ROOT / "lab" / "Dockerfile").read_text()


def test_env_example_has_no_values_for_secrets():
    for line in (ROOT / ".env.example").read_text().splitlines():
        if re.match(r"^(LAB_PG_SUPERUSER_PASSWORD|GOLIATH_PORTAL_DB_PASSWORD|GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET)=", line):
            assert line.endswith("="), line


def test_pins_are_full_commit_shas():
    pins = dict(
        l.split("=", 1) for l in (ROOT / "lab" / "pins.env").read_text().splitlines() if l and not l.startswith("#")
    )
    for key in ("GOLIATH_APP_REF", "GOLIATH_OMICS_REF"):
        assert re.fullmatch(r"[0-9a-f]{40}", pins[key]), key


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_runs_as_script(nb: Path):
    res = subprocess.run([sys.executable, nb.name], cwd=nb.parent, capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr[-2000:]


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_passes_marimo_check(nb: Path):
    res = subprocess.run([sys.executable, "-m", "marimo", "check", str(nb)], capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr


_MERMAID_FENCE_RE = re.compile(r"^```mermaid\s*\n(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL)
_SUBGRAPH_OPEN_RE = re.compile(r"^\s*subgraph\s+\S+\s+\[")
_SUBGRAPH_CLOSE_RE = re.compile(r"^\s*end\s*$")


def _assert_valid_mermaid(body: str, context: str) -> None:
    lines = [line for line in body.splitlines() if line.strip()]
    assert lines, f"{context}: empty mermaid diagram"
    assert lines[0].startswith(("flowchart ", "graph ", "sequenceDiagram", "erDiagram")), (
        f"{context}: unexpected mermaid header {lines[0]!r}"
    )
    depth = 0
    for line in lines[1:]:
        if _SUBGRAPH_OPEN_RE.match(line):
            depth += 1
        elif _SUBGRAPH_CLOSE_RE.match(line):
            depth -= 1
            assert depth >= 0, f"{context}: unmatched 'end'"
        if "classDef " not in line:
            assert ";" not in line, f"{context}: unexpected semicolon in {line!r}"
    assert depth == 0, f"{context}: unclosed subgraph(s), depth={depth}"


def test_diagrams_and_embedded_mermaid_blocks():
    diagrams_dir = ROOT / "diagrams"
    assert (diagrams_dir / "README.md").is_file()
    mmd_files = sorted(diagrams_dir.glob("*.mmd"))
    assert len(mmd_files) >= 41
    for mmd in mmd_files:
        _assert_valid_mermaid(mmd.read_text(encoding="utf-8"), mmd.name)

    for md in [ROOT / "README.md", *(d / f"{int(d.name.split(' - ')[0]):02d}_content.md" for d in module_dirs())]:
        text = md.read_text(encoding="utf-8")
        for idx, match in enumerate(_MERMAID_FENCE_RE.finditer(text), start=1):
            _assert_valid_mermaid(match.group("body"), f"{md.name}#{idx}")

    embedded_pairs = [
        ("3 - Assays, Analytes & Process Packs/03_content.md", "sample_prep_rnaseq.mmd"),
        ("3 - Assays, Analytes & Process Packs/03_content.md", "sample_prep_proteomics.mmd"),
        ("7 - QC at Every Level/07_content.md", "sample_prep_remediate.mmd"),
        ("9 - Workflows, Workers & the Execution Record/09_content.md", "sample_prep.mmd"),
        ("9 - Workflows, Workers & the Execution Record/09_content.md", "event_wait_ack.mmd"),
        ("10 - Studies, Partitions & the Claim Gate/10_content.md", "samd_research.mmd"),
        ("10 - Studies, Partitions & the Claim Gate/10_content.md", "study_validation_lifecycle.mmd"),
    ]
    for md_rel, mmd_name in embedded_pairs:
        md_text = (ROOT / md_rel).read_text(encoding="utf-8")
        expected_body = (diagrams_dir / mmd_name).read_text(encoding="utf-8").strip()
        bodies = [m.group("body").strip() for m in _MERMAID_FENCE_RE.finditer(md_text)]
        assert expected_body in bodies, f"{md_rel} is out of sync with diagrams/{mmd_name}"
