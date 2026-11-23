import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 8: Configuration as a Controlled Artifact")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import module_08_overlay as m8

    mo.md(
        """
        # Module 8: Configuration as a Controlled Artifact
        *Genomics with GoliathOmics · Goliath Research Academy*

        One action section (`alignment_qc`) through the four layers, then analyte fill-missing.
        Toggle layers and see which layer owns each effective value. `null` deletes a key.
        """
    )
    return m8, mo


@app.cell
def _(mo):
    use_profile = mo.ui.checkbox(value=True, label="Pipeline profile sets alignment_guardrails.min_mapping_rate 0.97")
    use_proc_null = mo.ui.checkbox(value=False, label="Procedure sets cycle_screening to null")
    use_instance = mo.ui.checkbox(value=False, label="Instance overlay sets min_mapping_rate 0.95")
    analyte = mo.ui.dropdown(options=["none", "cfdna", "buffy_coat"], value="cfdna", label="primary_analyte")
    mo.vstack([use_profile, use_proc_null, use_instance, analyte])
    return analyte, use_instance, use_proc_null, use_profile


@app.cell
def _(analyte, m8, mo, use_instance, use_proc_null, use_profile):
    # Key names follow GoliathOmics' alignment_qc section; the cfdna patch is the alignment_qc part of
    # analyte_profiles.py at the pinned commit (bisulfite and guardrail sub-blocks shortened).
    site = {"alignment_guardrails": {"enabled": True, "min_mapping_rate": 0.98}, "cycle_screening": {"enabled": True}}
    layers = {
        "site": site,
        "profile": {"alignment_guardrails": {"min_mapping_rate": 0.97}} if use_profile.value else None,
        "procedure": {"cycle_screening": None} if use_proc_null.value else None,
        "instance": {"alignment_guardrails": {"min_mapping_rate": 0.95}} if use_instance.value else None,
    }
    guardrails = {"enabled": True, "min_mapping_rate": 0.98, "flagstat_enabled": True, "min_properly_paired_rate": 0.90}
    bisulfite = {"enabled": True, "min_conversion_rate_pct": 99.0, "max_non_cpg_methylation_pct": 2.0}
    patches = {
        "cfdna": {"auto_profile_from_analyte": True, "fragmentomics": {"enabled": True, "profile": "cfdna"},
                  "bisulfite_conversion": bisulfite, "alignment_guardrails": guardrails},
        "buffy_coat": {"auto_profile_from_analyte": False, "bisulfite_conversion": bisulfite, "alignment_guardrails": guardrails},
    }
    merged, prov = m8.resolve(layers, patches.get(analyte.value))
    flat = sorted(prov.items())
    mo.md("\n".join(["| Effective key | Set by |", "|---|---|", *[f"| `{k}` | {v} |" for k, v in flat], "",
                     "The analyte never overrides `min_mapping_rate` once any layer set it; it only adds what is missing."]))
    return


if __name__ == "__main__":
    app.run()
