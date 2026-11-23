"""Teaching helpers for Module 7: guardrail what-if.

DEFAULTS mirrors the defaults in GoliathOmics schemas/config/sample_prep_guardrails.schema.json and
the RNA / proteomics QC configs (packages/rnaalignmentqc, packages/proteomicsqc) at the pinned
commit. ``load_schema_defaults`` reads the real schema from the pinned checkout so a test can prove
the copy has not drifted.

The decision function is a simplified teaching model of the SamplePrep flow
(docs/usage/03-sample-prep-and-qc.md): pass, remediate once (fastp trim + forced realign) for
read-quality failures, otherwise reject (archive_qc_only). The platform's real logic lives in
packages/methylalignmentqc and methylextractionqc.
"""

from __future__ import annotations

import json
from pathlib import Path

# gate -> metric -> (comparison, default)
DEFAULTS: dict[str, dict[str, tuple[str, float]]] = {
    "core": {
        "min_q30_percent": (">=", 85.0),
        "min_mean_quality": (">=", 35.0),
        "min_pf_percent": (">=", 90.0),
        "median_insert_min_bp": (">=", 150),
        "median_insert_max_bp": ("<=", 300),
    },
    "alignment": {
        "min_mapping_rate": (">=", 0.98),
        "min_properly_paired_rate": (">=", 0.9),
        "max_secondary_supplementary_rate": ("<=", 0.05),
    },
    "bisulfite": {
        "min_conversion_rate_pct": (">=", 99.0),
        "max_non_cpg_methylation_pct": ("<=", 2.0),
    },
    "extraction": {
        "min_cpg_weighted_mean_coverage": (">=", 10.0),
        "max_chg_methylation_level": ("<=", 0.02),
        "max_chh_methylation_level": ("<=", 0.02),
        "min_autosomal_coverage_uniformity_ratio": (">=", 0.5),
    },
    "rna": {
        "min_mapping_rate": (">=", 0.5),
        "min_uniquely_mapped_rate": (">=", 0.4),
        "min_genes_detected": (">=", 5000),
        "min_input_reads": (">=", 1_000_000),
    },
    "proteomics": {
        "min_proteins_identified": (">=", 300),
        "max_missing_fraction": ("<=", 0.9),
    },
}

SCHEMA_DEFS = {
    "core": "CoreGuardrailsFull",
    "alignment": "AlignmentGuardrailsFull",
    "bisulfite": "BisulfiteConversionFull",
    "extraction": "ExtractionQcGuardrailFull",
}

REMEDIABLE = {"min_q30_percent", "min_mean_quality"}  # read-end quality problems fastp can trim


def evaluate(gate: str, metrics: dict[str, float], overrides: dict[str, float] | None = None) -> dict[str, bool]:
    """Per-threshold pass/fail for the metrics supplied (missing metrics are skipped)."""
    out: dict[str, bool] = {}
    for key, (op, default) in DEFAULTS[gate].items():
        threshold = (overrides or {}).get(key, default)
        metric = metrics.get(key)
        if metric is None:
            continue
        out[key] = metric >= threshold if op == ">=" else metric <= threshold
    return out


def decide(failures: list[str], already_remediated: bool) -> str:
    if not failures:
        return "pass"
    if not already_remediated and set(failures) <= REMEDIABLE:
        return "remediate: sample.trim_fastq (fastp) -> forced realign -> QC retry"
    return "reject: archive_qc_only"


def load_schema_defaults(schema_path: str | Path) -> dict[str, dict[str, float]]:
    data = json.loads(Path(schema_path).read_text())
    defs = data.get("$defs", {})
    out: dict[str, dict[str, float]] = {}
    for gate, name in SCHEMA_DEFS.items():
        props = defs.get(name, {}).get("properties", {})
        out[gate] = {k: v.get("default") for k, v in props.items() if isinstance(v, dict) and "default" in v}
    return out
