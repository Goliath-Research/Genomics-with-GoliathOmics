"""Teaching helpers for Module 3: in-silico bisulfite conversion and the process-pack model.

The pack table mirrors GoliathOmics docs/operators/process-packs.md and docs/ANALYTE_PROFILES.md at
the pinned commit. It is a study aid, not the platform's resolver.
"""

from __future__ import annotations

COMPLEMENT = str.maketrans("ACGTN", "TGCAN")


def revcomp(seq: str) -> str:
    return seq.upper().translate(COMPLEMENT)[::-1]


def cpg_positions(seq: str) -> list[int]:
    """0-based positions of the C in every CpG on the top strand."""
    s = seq.upper()
    return [i for i in range(len(s) - 1) if s[i] == "C" and s[i + 1] == "G"]


def bisulfite_convert(seq: str, methylated: set[int] | frozenset[int] = frozenset(), conversion_rate: float = 1.0) -> str:
    """Top-strand conversion: unmethylated C -> T. ``methylated`` holds 0-based C positions.

    ``conversion_rate`` < 1 leaves a deterministic fraction of unmethylated Cs unconverted
    (every k-th one), so results are reproducible in tests and notebooks.
    """
    if not 0.0 <= conversion_rate <= 1.0:
        raise ValueError("conversion_rate must be in [0, 1]")
    out = []
    debt = 0.0  # accumulates the unconverted share; emit an unconverted C each time it reaches 1
    for i, base in enumerate(seq.upper()):
        if base == "C" and i not in methylated:
            debt += 1.0 - conversion_rate
            if debt >= 1.0 - 1e-9:
                debt -= 1.0
                out.append("C")
            else:
                out.append("T")
        else:
            out.append(base)
    return "".join(out)


def estimated_conversion_rate(reference: str, converted: str) -> float:
    """Share of non-CpG reference Cs read as T (the usual mammalian proxy)."""
    ref = reference.upper()
    cpg = set(cpg_positions(ref))
    non_cpg = [i for i, b in enumerate(ref) if b == "C" and i not in cpg]
    if not non_cpg:
        return float("nan")
    converted_count = sum(1 for i in non_cpg if converted[i] == "T")
    return converted_count / len(non_cpg)


def methylation_calls(reference: str, read: str) -> dict[int, str]:
    """At each reference CpG, 'M' if the read kept C, 'U' if it shows T."""
    return {i: ("M" if read[i] == "C" else "U") for i in cpg_positions(reference) if read[i] in "CT"}


MODALITIES = {
    "methylation": {
        "sample_prep": "sample_prep.program.json",
        "study": "study_validation_lifecycle.program.json",
        "profile": "samd_research",
        "output": "{chr}-CG.h5",
    },
    "rnaseq": {
        "sample_prep": "sample_prep_rnaseq.program.json",
        "study": "rnaseq_study_lifecycle.program.json",
        "profile": "rnaseq_research",
        "output": "{sample_id}.expression.h5",
    },
    "proteomics": {
        "sample_prep": "sample_prep_proteomics.program.json",
        "study": "proteomics_study_lifecycle.program.json",
        "profile": "proteomics_research",
        "output": "abundance.h5",
    },
}

# procedure -> (analyteExpectation, libraryProtocol, samplePrepProgram, lifecycleProgram)
PROCEDURES = {
    "buffy_wgbs_pangenome_gene_fc": ("buffy_coat", "wgbs_pangenome", "sample_prep", "study_validation_lifecycle"),
    "buffy_wgbs_linear_gene_fc": ("buffy_coat", "wgbs_linear", "sample_prep", "study_validation_lifecycle"),
    "buffy_wgbs_linear_mojo_gene_fc": ("buffy_coat", "wgbs_linear", "sample_prep", "study_validation_lifecycle"),
    "buffy_wgbs_mvalue_residual_gene_fc": ("buffy_coat", "wgbs_pangenome", "sample_prep", "study_validation_lifecycle_residual"),
    "cfdna_wgbs_plasma": ("cfdna", "wgbs_linear", "sample_prep", "study_validation_lifecycle_no_deconv"),
    "cfdna_emseq_targeted": ("cfdna", "emseq_targeted", "sample_prep_emseq", "study_validation_lifecycle_no_deconv"),
    "cfdna_emseq_mhl_survival": ("cfdna", "emseq_targeted", "sample_prep_emseq", "study_validation_mhl_survival"),
    "plant_wgbs_gene_fc": ("plant_tissue", "wgbs_linear", "sample_prep", "plant_stress_study_lifecycle"),
}

ANALYTE_SWITCHES = {
    "cfdna": {"fragmentomics": True, "max_chh_chg": 0.02, "non_cpg_cap_opened": False,
              "cell_deconvolution": "Houseman or HiTIMED plasma tree"},
    "buffy_coat": {"fragmentomics": False, "max_chh_chg": 0.02, "non_cpg_cap_opened": False,
                   "cell_deconvolution": "Houseman or HiTIMED immune subtree"},
    "tissue": {"fragmentomics": False, "max_chh_chg": 0.02, "non_cpg_cap_opened": False,
               "cell_deconvolution": "HiTIMED tumor/immune/stromal tree"},
    "plant_tissue": {"fragmentomics": False, "max_chh_chg": 1.0, "non_cpg_cap_opened": True,
                     "cell_deconvolution": "not applicable"},
    "combined": {"fragmentomics": False, "max_chh_chg": None, "non_cpg_cap_opened": False,
                 "cell_deconvolution": "profile decides"},
}


def choose(modality: str, procedure: str | None = None, analyte: str | None = None) -> dict:
    """Return the programs and switches a study with these choices would use."""
    if modality not in MODALITIES:
        raise ValueError(f"unknown modality {modality!r}")
    plan = dict(MODALITIES[modality], modality=modality)
    if modality != "methylation":
        plan["note"] = "analyte packs and bisulfite QC apply to methylation only"
        return plan
    if procedure is None:
        raise ValueError("methylation studies name a pipelineProcedure")
    expected_analyte, protocol, sample_prep, lifecycle = PROCEDURES[procedure]
    analyte = analyte or expected_analyte
    if analyte != expected_analyte:
        raise ValueError(f"primary_analyte {analyte!r} does not match {procedure} analyteExpectation {expected_analyte!r}")
    plan.update(
        procedure=procedure,
        libraryProtocol=protocol,
        analyte=analyte,
        sample_prep=f"{sample_prep}.program.json",
        study=f"{lifecycle}.program.json",
        **ANALYTE_SWITCHES[analyte],
    )
    return plan
