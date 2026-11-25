import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 3: Assays, Analytes & Process Packs")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import module_03_assays as m3

    mo.md(
        """
        # Module 3: Assays, Analytes & Process Packs
        *Genomics with GoliathOmics · Goliath Research Academy*

        Two tools in one notebook:

        1. **In-silico bisulfite conversion**: see why methylation becomes a C/T difference and how
           the conversion rate is estimated.
        2. **Pack chooser**: pick a modality, procedure and analyte and see what GoliathOmics runs.

        Reads in the public run SRR28293403 are *already* converted (Module 4 looks at them), so
        here we start from a short reference you can edit.
        """
    )
    return m3, mo


@app.cell
def _(mo):
    reference = mo.ui.text(value="ACGTTCCGACTCAGCGTTACCGGCATCGA", label="Reference (top strand)", full_width=True)
    reference
    return (reference,)


@app.cell
def _(m3, mo, reference):
    ref = reference.value.upper().replace(" ", "")
    cpgs = m3.cpg_positions(ref)
    methylated = mo.ui.multiselect(
        options={f"CpG at {p}": p for p in cpgs},
        value=[f"CpG at {p}" for p in cpgs[: max(1, len(cpgs) // 2)]],
        label="Methylated CpGs",
    )
    rate = mo.ui.slider(0.80, 1.0, step=0.01, value=1.0, label="Bisulfite conversion efficiency")
    mo.hstack([methylated, rate])
    return methylated, rate, ref


@app.cell
def _(m3, methylated, mo, rate, ref):
    read = m3.bisulfite_convert(ref, set(methylated.value), rate.value)
    est = m3.estimated_conversion_rate(ref, read)
    calls = m3.methylation_calls(ref, read)
    mo.md(
        f"""
        | | |
        |---|---|
        | Reference | `{ref}` |
        | Converted read | `{read}` |
        | Calls at CpGs | {", ".join(f"{p}:{c}" for p, c in calls.items()) or "none"} |
        | Estimated conversion rate (non-CpG C → T) | **{est:.2%}** |

        GoliathOmics' default guardrail is `min_conversion_rate_pct` **99** (Module 7). Lower the
        slider and watch unconverted Cs appear: each one at a CpG would be miscalled as methylated.
        """
    )
    return


@app.cell(hide_code=True)
def _(m3, mo):
    modality = mo.ui.dropdown(options=list(m3.MODALITIES), value="methylation", label="Modality")
    procedure = mo.ui.dropdown(options=list(m3.PROCEDURES), value="buffy_wgbs_linear_gene_fc", label="Procedure (methylation)")
    mo.vstack([mo.md("## Pack chooser"), mo.hstack([modality, procedure])])
    return modality, procedure


@app.cell
def _(m3, mo, modality, procedure):
    plan = m3.choose(modality.value, procedure.value if modality.value == "methylation" else None)
    table = mo.md(
        "\n".join(["| Setting | Value |", "|---|---|"] + [f"| {k} | `{v}` |" for k, v in plan.items()])
    )
    prep_mmd = m3.load_diagram(plan["sample_prep"])
    study_mmd = m3.load_diagram(plan["study"])
    mo.vstack(
        [
            table,
            mo.md(f"### SamplePrep workflow (`{plan['sample_prep']}`)"),
            mo.mermaid(prep_mmd),
            mo.md(f"### Study lifecycle workflow (`{plan['study']}`)"),
            mo.mermaid(study_mmd),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
