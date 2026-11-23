"""Unit tests for the teaching helpers in Modules 3-8."""

from __future__ import annotations

import math

import numpy as np
import pytest

from conftest import load_module

m03 = load_module(3, "module_03_assays.py")
m04 = load_module(4, "module_04_formats.py")
m05 = load_module(5, "module_05_alignment.py")
m06 = load_module(6, "module_06_features.py")
m07 = load_module(7, "module_07_qc.py")
m08 = load_module(8, "module_08_overlay.py")


# Module 3 -------------------------------------------------------------------------------------
def test_bisulfite_keeps_methylated_cpg_and_converts_the_rest():
    ref = "ACGTTCGACCA"
    cpgs = m03.cpg_positions(ref)
    assert cpgs == [1, 5]
    read = m03.bisulfite_convert(ref, methylated={1})
    assert read == "ACGTTTGATTA"
    assert m03.methylation_calls(ref, read) == {1: "M", 5: "U"}
    assert m03.estimated_conversion_rate(ref, read) == 1.0


def test_incomplete_conversion_is_deterministic():
    ref = "C" * 100
    read = m03.bisulfite_convert(ref, conversion_rate=0.9)
    assert read.count("C") == 10
    assert read == m03.bisulfite_convert(ref, conversion_rate=0.9)
    with pytest.raises(ValueError):
        m03.bisulfite_convert(ref, conversion_rate=1.5)


def test_choose_covers_every_modality_and_procedure():
    assert set(m03.MODALITIES) == {"methylation", "rnaseq", "proteomics"}
    assert len(m03.PROCEDURES) == 8
    assert set(m03.ANALYTE_SWITCHES) == {"buffy_coat", "cfdna", "tissue", "plant_tissue", "combined"}
    for proc in m03.PROCEDURES:
        plan = m03.choose("methylation", proc)
        assert plan["sample_prep"].endswith(".program.json")
    assert m03.choose("rnaseq")["profile"] == "rnaseq_research"
    assert m03.choose("methylation", "cfdna_emseq_targeted")["fragmentomics"] is True
    assert m03.choose("methylation", "plant_wgbs_gene_fc")["non_cpg_cap_opened"] is True
    with pytest.raises(ValueError):
        m03.choose("methylation", "cfdna_wgbs_plasma", analyte="buffy_coat")
    with pytest.raises(ValueError):
        m03.choose("metabolomics")


# Module 4 -------------------------------------------------------------------------------------
def test_public_fixture_statistics():
    r1 = m04.read_fastq(m04.FIXTURES / "SRR28293403_1.first1000.fastq.gz")
    r2 = m04.read_fastq(m04.FIXTURES / "SRR28293403_2.first1000.fastq.gz")
    assert len(r1) == len(r2) == 1000
    assert {len(r.seq) for r in r1} == {151}
    # Bisulfite signature: read 1 is C-depleted, read 2 is G-depleted.
    assert m04.base_composition(r1)["C"] < 0.06
    assert m04.base_composition(r2)["G"] < 0.10
    assert m04.q30_percent(r1) == pytest.approx(87.5, abs=0.1)
    assert 0.30 < m04.adapter_fraction(r1) < 0.35


def test_sam_flag_and_cigar():
    assert m04.decode_flag(99)[:2] == [m04.SAM_FLAGS[0][1], m04.SAM_FLAGS[1][1]]
    assert m04.parse_cigar("10M2I5M3D4S") == [(10, "M"), (2, "I"), (5, "M"), (3, "D"), (4, "S")]
    assert m04.cigar_lengths("10M2I5M3D4S") == (18, 21)


# Module 5 -------------------------------------------------------------------------------------
def test_three_letter_alignment_places_a_converted_read():
    ref = m05.synthetic_reference(800, seed=3, cpg_boost=0.3)
    truth = 400
    read = m03.bisulfite_convert(ref[truth : truth + 60])
    hits = m05.best_hits(read, ref, three_letter=True)
    assert (truth, 0) in hits
    plain = m05.best_hits(read, ref, three_letter=False)
    assert plain[0][1] > 0


def test_mapq_like_is_zero_for_ties():
    assert m05.mapq_like([(1, 0), (9, 0)], 0, 60) == 0
    assert m05.mapq_like([(1, 0)], None, 60) == 60


# Module 6 -------------------------------------------------------------------------------------
def test_beta_values_respect_min_coverage():
    beta = m06.beta_values(np.array([3, 1, 0]), np.array([1, 1, 0]))
    assert beta[0] == 0.75 and math.isnan(beta[1]) and math.isnan(beta[2])
    assert m06.cpg_weighted_mean_coverage(np.array([3, 1, 0]), np.array([1, 1, 0])) == 3.0


def test_cpm_rows_sum_to_a_million():
    counts = np.array([[10, 30, 60], [1, 1, 2]])
    assert np.allclose(m06.cpm(counts).sum(axis=1), 1e6)


def test_proteomics_normalize_fills_gaps():
    x = m06.proteomics_normalize(np.array([[100.0, 0.0, 50.0], [200.0, 80.0, 0.0]]))
    assert not np.isnan(x).any()


def test_feature_h5_contract(tmp_path):
    path = m06.write_feature_h5(tmp_path / "s.h5", "HG00621", "gene_fc", {"B": 2.0, "A": 1.0}, source="course")
    ids, values, attrs = m06.read_feature_h5(path)
    assert ids == ["A", "B"] and list(values) == [1.0, 2.0]
    assert attrs["n_features"] == 2 and attrs["sample_id"] == "HG00621"


# Module 7 -------------------------------------------------------------------------------------
def test_guardrail_decisions():
    res = m07.evaluate("core", {"min_q30_percent": 80.0, "min_pf_percent": 95.0})
    assert res == {"min_q30_percent": False, "min_pf_percent": True}
    assert m07.decide([], False) == "pass"
    assert m07.decide(["min_q30_percent"], False).startswith("remediate: sample.trim_fastq")
    assert m07.decide(["min_q30_percent"], True).startswith("reject")
    assert m07.decide(["min_mapping_rate"], False).startswith("reject")
    assert m07.evaluate("core", {"min_q30_percent": 80.0}, {"min_q30_percent": 75.0}) == {"min_q30_percent": True}


# Module 8 -------------------------------------------------------------------------------------
def test_overlay_order_null_delete_and_provenance():
    merged, prov = m08.resolve(
        {
            "site": {"qc": {"min_q30_percent": 80, "mode": "strict"}},
            "profile": {"qc": {"min_q30_percent": 85}},
            "procedure": None,
            "instance": {"qc": {"mode": None}},
        },
        analyte_patch={"qc": {"min_q30_percent": 99, "fragmentomics": True}},
    )
    assert merged == {"qc": {"min_q30_percent": 85, "fragmentomics": True}}
    assert prov == {"qc.min_q30_percent": "profile", "qc.fragmentomics": "analyte (fill-missing)"}
