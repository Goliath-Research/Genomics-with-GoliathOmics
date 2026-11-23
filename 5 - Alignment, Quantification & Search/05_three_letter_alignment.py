import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 5: Alignment, Quantification & Search")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    sys.path.insert(0, str(here.parent / "3 - Assays, Analytes & Process Packs"))
    import module_03_assays as m3
    import module_05_alignment as m5

    mo.md(
        """
        # Module 5: Alignment, Quantification & Search
        *Genomics with GoliathOmics · Goliath Research Academy*

        A synthetic 2,000-base reference (seeded random bases, not a real genome). We cut a read,
        bisulfite-convert it, and place it two ways: naively, and in three-letter (C→T) space.
        """
    )
    return m3, m5, mo


@app.cell
def _(mo):
    start = mo.ui.slider(0, 1900, value=640, label="Read start on the reference")
    length = mo.ui.slider(30, 100, value=60, label="Read length")
    methylated_share = mo.ui.slider(0.0, 1.0, step=0.1, value=0.5, label="Share of CpGs methylated")
    mo.vstack([start, length, methylated_share])
    return length, methylated_share, start


@app.cell
def _(length, m3, m5, methylated_share, mo, start):
    reference = m5.synthetic_reference(2000, seed=7, cpg_boost=0.3)
    true_pos = start.value
    fragment = reference[true_pos : true_pos + length.value]
    cpgs = m3.cpg_positions(fragment)
    meth = set(cpgs[: round(len(cpgs) * methylated_share.value)])
    read = m3.bisulfite_convert(fragment, meth)

    rows = []
    for label, three in (("naive (4-letter)", False), ("three-letter (C→T)", True)):
        hits = m5.best_hits(read, reference, three_letter=three)
        runner = m5.second_best(read, reference, three, hits[0][0])
        rows.append(
            f"| {label} | {', '.join(str(p) for p, _ in hits[:5])} | {hits[0][1]} | {runner} | "
            f"{m5.mapq_like(hits, runner, len(read))} | {'yes' if any(p == true_pos for p, _ in hits) else 'no'} |"
        )
    mo.md(
        "\n".join(
            [
                f"True position **{true_pos}**, {len(cpgs)} CpGs in the read, {len(meth)} methylated.",
                "",
                "| Strategy | Best position(s) | Mismatches | Runner-up mismatches | MAPQ-like | Found true position |",
                "|---|---|---|---|---|---|",
                *rows,
                "",
                "Naive alignment counts every converted C as a mismatch, so a read with many unmethylated "
                "Cs looks like a poor match everywhere. In C→T space the conversion disappears; the price "
                "is a less complex alphabet and more ties, which is why bisulfite MAPQ needs care.",
            ]
        )
    )
    return


if __name__ == "__main__":
    app.run()
