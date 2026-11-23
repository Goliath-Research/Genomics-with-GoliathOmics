import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Module 10: Studies, Partitions & the Claim Gate")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np

    mo.md(
        """
        # Module 10: Why holdouts matter
        *Genomics with GoliathOmics · Goliath Research Academy*

        Pure noise: random features, random labels (no person, sample or real measurement). Any
        accuracy above 50% on the test split is an artifact of how features were chosen.
        """
    )
    return mo, np


@app.cell
def _(mo):
    n_features = mo.ui.slider(500, 20000, step=500, value=5000, label="Features (CpGs, genes, proteins)")
    k = mo.ui.slider(5, 100, step=5, value=20, label="Features kept")
    mo.vstack([n_features, k])
    return k, n_features


@app.cell
def _(k, mo, n_features, np):
    rng = np.random.default_rng(42)
    n = 60
    x = rng.normal(size=(n, n_features.value))
    y = np.array([0, 1] * (n // 2))
    train = np.arange(n) < 40
    test = ~train

    def top_k(rows):
        diff = np.abs(x[rows][y[rows] == 1].mean(0) - x[rows][y[rows] == 0].mean(0))
        return np.argsort(diff)[-k.value:]

    def centroid_accuracy(features):
        c1 = x[train][y[train] == 1][:, features].mean(0)
        c0 = x[train][y[train] == 0][:, features].mean(0)
        xt = x[test][:, features]
        pred = (np.linalg.norm(xt - c1, axis=1) < np.linalg.norm(xt - c0, axis=1)).astype(int)
        return (pred == y[test]).mean()

    leak = centroid_accuracy(top_k(np.ones(n, bool)))
    honest = centroid_accuracy(top_k(train))
    mo.md(
        f"""
        | Feature selection on | Test accuracy |
        |---|---|
        | all 60 samples (**leak**) | **{leak:.0%}** |
        | the 40 training samples only | **{honest:.0%}** |

        The leaked number looks like a result. It is not. This is why GoliathOmics refuses to let
        `locked_test` / `pivotal_validation` samples back into training and blocks clinical claims
        before `pivotal_validation`.
        """
    )
    return


if __name__ == "__main__":
    app.run()
