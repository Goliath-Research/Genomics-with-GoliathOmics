"""Teaching helpers for Module 6: from counts to per-sample feature matrices.

Implements the arithmetic GoliathOmics documents for each modality, on small numeric arrays:

* methylation: per-CpG methylated / unmethylated counts -> beta values with a coverage filter;
* RNA-seq: counts -> CPM / log-CPM;
* proteomics: intensities -> log2, per-sample median normalization, per-protein minimum imputation.

``write_feature_h5`` writes the shared samples x features contract (``feature_id`` + ``value`` plus
optional aligned vectors and attrs ``source``/``kind``/``n_features``/``sample_id``) used by
GoliathOmics ``omics_features.feature_store``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np


def beta_values(m_c: np.ndarray, u_c: np.ndarray, min_coverage: int = 4) -> np.ndarray:
    """Beta = mC / (mC + uC); NaN where coverage < ``min_coverage`` (GoliathExtractor default 4)."""
    m_c = np.asarray(m_c, dtype=float)
    u_c = np.asarray(u_c, dtype=float)
    cov = m_c + u_c
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.where(cov >= min_coverage, m_c / cov, np.nan)
    return beta


def cpg_weighted_mean_coverage(m_c: np.ndarray, u_c: np.ndarray) -> float:
    """Mean coverage over covered CpGs (sites with coverage 0 are not counted)."""
    cov = np.asarray(m_c, dtype=float) + np.asarray(u_c, dtype=float)
    covered = cov[cov > 0]
    return float(covered.mean()) if covered.size else 0.0


def global_methylation(m_c: np.ndarray, u_c: np.ndarray) -> float:
    total = float(np.sum(m_c) + np.sum(u_c))
    return float(np.sum(m_c)) / total if total else float("nan")


def cpm(counts: np.ndarray) -> np.ndarray:
    counts = np.asarray(counts, dtype=float)
    lib = counts.sum(axis=-1, keepdims=True)
    return counts / lib * 1e6


def log_cpm(counts: np.ndarray, prior: float = 1.0) -> np.ndarray:
    return np.log2(cpm(np.asarray(counts, dtype=float) + prior))


def proteomics_normalize(intensities: np.ndarray) -> np.ndarray:
    """samples x proteins: log2, subtract each sample's median, fill gaps with the protein minimum."""
    x = np.log2(np.where(np.asarray(intensities, dtype=float) > 0, intensities, np.nan))
    x = x - np.nanmedian(x, axis=1, keepdims=True)
    col_min = np.nanmin(x, axis=0)
    rows, cols = np.where(np.isnan(x))
    x[rows, cols] = col_min[cols]
    return x


def write_feature_h5(path: str | Path, sample_id: str, kind: str, values: Mapping[str, float], source: str,
                     aux: Mapping[str, Mapping[str, float]] | None = None) -> Path:
    import h5py

    features = sorted(values)
    path = Path(path)
    with h5py.File(path, "w") as h5:
        dt = h5py.string_dtype(encoding="utf-8")
        h5.create_dataset("feature_id", data=np.asarray(features, dtype=object), dtype=dt)
        h5.create_dataset("value", data=np.asarray([float(values[f]) for f in features]))
        for name, mapping in (aux or {}).items():
            h5.create_dataset(name, data=np.asarray([float(mapping.get(f, np.nan)) for f in features]))
        h5.attrs.update({"source": source, "kind": kind, "n_features": len(features), "sample_id": sample_id})
    return path


def read_feature_h5(path: str | Path) -> tuple[list[str], np.ndarray, dict]:
    import h5py

    with h5py.File(path, "r") as h5:
        ids = [f.decode() if isinstance(f, bytes) else str(f) for f in h5["feature_id"][:]]
        return ids, np.asarray(h5["value"][:], dtype=float), dict(h5.attrs)
