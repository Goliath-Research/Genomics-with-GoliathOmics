import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 6: From Alignments to Feature Matrices")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import module_06_features as m6

    mo.md(
        """
        # Module 6: From Alignments to Feature Matrices
        *Genomics with GoliathOmics · Goliath Research Academy*

        The numbers below are **synthetic counts for arithmetic only**. They belong to no person,
        sample or customer. Each modality ends in the same shape: one value per feature per sample.
        """
    )
    return m6, mo, np


@app.cell
def _(mo):
    min_cov = mo.ui.slider(1, 20, value=4, label="Minimum CpG coverage (GoliathExtractor default 4)")
    min_cov
    return (min_cov,)


@app.cell
def _(m6, min_cov, mo, np):
    m_c = np.array([9, 0, 3, 12, 1, 7, 0, 5])
    u_c = np.array([1, 10, 0, 4, 2, 7, 0, 15])
    beta = m6.beta_values(m_c, u_c, min_cov.value)
    rows = [f"| CpG {i} | {m} | {u} | {m + u} | {'' if np.isnan(b) else f'{b:.2f}'} |" for i, (m, u, b) in enumerate(zip(m_c, u_c, beta))]
    mo.md(
        "\n".join(
            ["### Methylation: counts → beta", "| Site | mC | uC | coverage | beta |", "|---|---|---|---|---|", *rows, "",
             f"CpG-weighted mean coverage **{m6.cpg_weighted_mean_coverage(m_c, u_c):.2f}**, "
             f"global methylation **{m6.global_methylation(m_c, u_c):.2%}**. Raise the slider: sites drop out, "
             "which is why `min_cpg_weighted_mean_coverage` is a QC gate (Module 7)."]
        )
    )
    return


@app.cell
def _(m6, mo, np):
    counts = np.array([[500, 1500, 0, 8000], [250, 3000, 10, 4000]])
    lc = m6.log_cpm(counts)
    intens = np.array([[2.0e6, 0, 5.0e5, 1.2e7], [4.1e6, 3.0e5, 0, 2.2e7]])
    pn = m6.proteomics_normalize(intens)
    fmt = lambda a: " | ".join(f"{v:.2f}" for v in a)
    mo.md(
        f"""
        ### RNA-seq: counts → log-CPM (prior 1)
        | | f1 | f2 | f3 | f4 |
        |---|---|---|---|---|
        | run A | {fmt(lc[0])} |
        | run B | {fmt(lc[1])} |

        ### Proteomics: log2, median-normalize, minimum imputation
        | | p1 | p2 | p3 | p4 |
        |---|---|---|---|---|
        | run A | {fmt(pn[0])} |
        | run B | {fmt(pn[1])} |

        Zero intensities are missing values; each is filled with that protein's minimum after
        normalization, as `pipeline.protein_de_select` documents.
        """
    )
    return


if __name__ == "__main__":
    app.run()
