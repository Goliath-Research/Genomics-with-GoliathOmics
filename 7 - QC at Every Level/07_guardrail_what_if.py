import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 7: QC at Every Level")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    sys.path.insert(0, str(here.parent / "4 - Genome & Data Representations"))
    import module_04_formats as m4
    import module_07_qc as m7

    mo.md(
        """
        # Module 7: QC at Every Level
        *Genomics with GoliathOmics · Goliath Research Academy*

        Move the metrics and thresholds and see which gate trips and what SamplePrep does next.
        Defaults are GoliathOmics' schema defaults. The decision rule is a simplified teaching model.
        """
    )
    return m4, m7, mo


@app.cell
def _(m4, mo):
    r1 = m4.read_fastq(m4.FIXTURES / "SRR28293403_1.first1000.fastq.gz")
    q30 = m4.q30_percent(r1)
    meanq = sum(sum(r.phred()) for r in r1) / sum(len(r.seq) for r in r1)
    mo.md(
        f"""
        **Real numbers from the fixture** (first 1,000 R1 reads of SRR28293403): %Q30 **{q30:.1f}**,
        mean quality **{meanq:.2f}**. The first reads of a run come from tile edges and are not
        representative; QC thresholds apply to the whole run, never to a 1,000-read sample.
        """
    )
    return meanq, q30


@app.cell
def _(meanq, mo, q30):
    s_q30 = mo.ui.slider(60.0, 100.0, step=0.5, value=round(q30, 1), label="%Q30")
    s_meanq = mo.ui.slider(20.0, 40.0, step=0.1, value=round(meanq, 1), label="Mean quality")
    s_map = mo.ui.slider(0.80, 1.0, step=0.005, value=0.985, label="Mapping rate")
    s_conv = mo.ui.slider(95.0, 100.0, step=0.1, value=99.5, label="Conversion rate %")
    s_cov = mo.ui.slider(1.0, 40.0, step=0.5, value=12.0, label="CpG-weighted mean coverage")
    t_meanq = mo.ui.slider(30.0, 38.0, step=0.5, value=35.0, label="Threshold: min_mean_quality")
    remediated = mo.ui.checkbox(label="Already remediated once")
    mo.vstack([s_q30, s_meanq, s_map, s_conv, s_cov, t_meanq, remediated])
    return remediated, s_conv, s_cov, s_map, s_meanq, s_q30, t_meanq


@app.cell
def _(m7, mo, remediated, s_conv, s_cov, s_map, s_meanq, s_q30, t_meanq):
    results = {
        "core": m7.evaluate("core", {"min_q30_percent": s_q30.value, "min_mean_quality": s_meanq.value},
                            {"min_mean_quality": t_meanq.value}),
        "alignment": m7.evaluate("alignment", {"min_mapping_rate": s_map.value}),
        "bisulfite": m7.evaluate("bisulfite", {"min_conversion_rate_pct": s_conv.value}),
        "extraction": m7.evaluate("extraction", {"min_cpg_weighted_mean_coverage": s_cov.value}),
    }
    failures = [k for gate in results.values() for k, ok in gate.items() if not ok]
    rows = [f"| {g} | {k} | {'pass' if ok else '**fail**'} |" for g, r in results.items() for k, ok in r.items()]
    mo.md("\n".join(["| Gate | Threshold | Result |", "|---|---|---|", *rows, "",
                     f"Next step: **{m7.decide(failures, remediated.value)}**"]))
    return


if __name__ == "__main__":
    app.run()
