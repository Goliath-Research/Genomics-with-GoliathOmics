"""The course's teaching copies match the pinned GoliathOmics checkout.

Skipped when ``.lab-src/GoliathOmics`` (or ``$GOLIATH_LAB_SRC``) is absent; CI clones the pin.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from conftest import load_module, load_official

m03 = load_module(3, "module_03_assays.py")
m06 = load_module(6, "module_06_features.py")
m07 = load_module(7, "module_07_qc.py")
m08 = load_module(8, "module_08_overlay.py")


def test_guardrail_defaults_match_schema(omics_src: Path):
    schema = m07.load_schema_defaults(omics_src / "schemas" / "config" / "sample_prep_guardrails.schema.json")
    for gate in m07.SCHEMA_DEFS:
        for key, (_, default) in m07.DEFAULTS[gate].items():
            assert schema[gate].get(key) == default, f"{gate}.{key}"


def test_procedure_table_matches_procedure_files(omics_src: Path):
    folder = omics_src / "workflow_engine" / "domain" / "profiles" / "procedures"
    files = sorted(folder.glob("*.procedure.json"))
    assert {f.name.removesuffix(".procedure.json") for f in files} == set(m03.PROCEDURES)
    for f in files:
        d = json.loads(f.read_text())
        analyte, protocol, sample_prep, lifecycle = m03.PROCEDURES[d["pipelineProcedure"]]
        expected = d["analyteExpectation"]
        # A list names the canonical analyte first, then accepted aliases (plant: leaf, root, ...).
        assert (expected[0] if isinstance(expected, list) else expected) == analyte
        assert d["libraryProtocol"] == protocol
        assert Path(d["samplePrepProgram"]).name == f"{sample_prep}.program.json"
        assert Path(d["lifecycleProgram"]).name == f"{lifecycle}.program.json"
        assert (omics_src / d["samplePrepProgram"]).is_file()
        assert (omics_src / d["lifecycleProgram"]).is_file()


def test_modality_programs_exist(omics_src: Path):
    fixtures = omics_src / "workflow_engine" / "domain" / "fixtures"
    for modality, plan in m03.MODALITIES.items():
        assert (fixtures / plan["sample_prep"]).is_file(), modality
        assert (fixtures / plan["study"]).is_file(), modality


def test_deep_merge_matches_official(omics_src: Path):
    deep_merge = load_official(omics_src, "packages/methylutils/methyl_utils/action_config_resolver.py").deep_merge

    rng = random.Random(11)

    def rand_tree(depth: int = 0) -> dict:
        out = {}
        for k in rng.sample("abcde", rng.randint(1, 4)):
            r = rng.random()
            out[k] = rand_tree(depth + 1) if r < 0.3 and depth < 3 else (None if r < 0.45 else rng.randint(0, 9))
        return out

    for _ in range(300):
        base, overlay = rand_tree(), rand_tree()
        assert m08.deep_merge(base, overlay) == deep_merge(base, overlay)


def test_feature_files_read_by_official_reader(omics_src: Path, tmp_path: Path):
    h5py = pytest.importorskip("h5py")
    read_feature_datasets = load_official(
        omics_src, "packages/omicsfeatures/omics_features/feature_store.py"
    ).read_feature_datasets

    path = m06.write_feature_h5(tmp_path / "x.h5", "HG00621", "gene_fc", {"G2": 0.5, "G1": 0.25}, source="course")
    with h5py.File(path, "r") as h5:
        ids, values = read_feature_datasets(h5)
    assert list(ids) == ["G1", "G2"] and list(values) == [0.25, 0.5]


def test_claim_gate_blocks_claims_before_pivotal(omics_src: Path):
    pytest.importorskip("pydantic")
    RegulatoryLifecycleConfig = load_official(
        omics_src, "packages/methylvalidation/methyl_validation/config.py"
    ).RegulatoryLifecycleConfig

    for stage in ("feasibility", "expanded_development", "internal_validation", "model_freeze"):
        with pytest.raises(ValueError):
            RegulatoryLifecycleConfig(stage=stage, allow_clinical_performance_claims=True)
    assert RegulatoryLifecycleConfig(stage="pivotal_validation", allow_clinical_performance_claims=True)


def test_module_9_run_alignment_sources_match_schema(omics_src: Path):
    """Module 9's table of steps that produce runs/alignments matches the pinned seed."""
    import re

    sql = (omics_src / "database" / "schema" / "22_omics_run_alignment_objects.sql").read_text()
    seeded = set(re.findall(r"\('(sample\.[a-z0-9_]+)',\s*'(omics/(?:SequencingRun|AlignmentResult))'", sql))
    assert seeded, "no wf_meta_object_source seed rows found"
    folder = next(p for p in (Path(__file__).resolve().parents[1]).iterdir() if p.name.startswith("9 - "))
    text = (folder / "09_content.md").read_text()
    for action, cls in seeded:
        row = next((ln for ln in text.splitlines() if ln.startswith("|") and cls in ln and action.split(".", 1)[1] in ln), None)
        assert row, f"module 9 does not list {action} -> {cls}"
