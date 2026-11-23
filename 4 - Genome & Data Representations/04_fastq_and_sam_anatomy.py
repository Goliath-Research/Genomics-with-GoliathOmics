import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 4: Genome & Data Representations")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import module_04_formats as m4

    mo.md(
        """
        # Module 4: Genome & Data Representations
        *Genomics with GoliathOmics · Goliath Research Academy*

        Real reads: the first 1,000 read pairs of public ENA run **SRR28293403** (WGBS of the
        1000 Genomes cell line HG00621), committed under `data/fixtures/` with checksums.
        """
    )
    return m4, mo


@app.cell
def _(m4):
    r1 = m4.read_fastq(m4.FIXTURES / "SRR28293403_1.first1000.fastq.gz")
    r2 = m4.read_fastq(m4.FIXTURES / "SRR28293403_2.first1000.fastq.gz")
    return r1, r2


@app.cell
def _(m4, mo, r1, r2):
    def row(label, recs):
        comp = m4.base_composition(recs)
        return (
            f"| {label} | {len(recs)} | {comp['A']:.1%} | {comp['C']:.1%} | {comp['G']:.1%} | {comp['T']:.1%} "
            f"| {m4.q30_percent(recs):.1f} | {m4.adapter_fraction(recs):.1%} |"
        )

    mo.md(
        "\n".join(
            [
                "| Mate | Reads | A | C | G | T | %Q30 | reads with adapter |",
                "|---|---|---|---|---|---|---|---|",
                row("R1", r1),
                row("R2", r2),
                "",
                "**Read the table.** In R1, C is nearly gone (unmethylated C became T). R2 is the "
                "complementary strand, so G is depleted instead. That is the bisulfite signature, and it "
                "is why ordinary aligners fail on these reads (Module 5). About a third of reads contain "
                "the TruSeq adapter: short inserts that `sample.trim_fastq_fastp` removes in the "
                "remediation loop (Module 7).",
            ]
        )
    )
    return


@app.cell
def _(m4, mo, r1):
    q = m4.per_cycle_mean_quality(r1)
    worst = sorted(range(len(q)), key=lambda i: q[i])[:5]
    mo.md(
        f"R1 per-cycle mean quality ranges from **{min(q):.1f}** to **{max(q):.1f}**. "
        f"Lowest cycles (0-based): {worst}. The `cycle screening` QC in Module 7 looks for dips like these."
    )
    return


@app.cell
def _(mo):
    flag = mo.ui.number(start=0, stop=4095, value=99, label="SAM FLAG")
    cigar = mo.ui.text(value="5S60M2I30M1D54M", label="CIGAR")
    mo.hstack([flag, cigar])
    return cigar, flag


@app.cell
def _(cigar, flag, m4, mo):
    try:
        ref_span, read_len = m4.cigar_lengths(cigar.value)
        cigar_text = f"reference span **{ref_span}**, read bases **{read_len}**"
    except ValueError as exc:
        cigar_text = str(exc)
    mo.md(f"FLAG {int(flag.value)} = `{', '.join(m4.decode_flag(int(flag.value))) or 'none'}` · CIGAR: {cigar_text}")
    return


if __name__ == "__main__":
    app.run()
