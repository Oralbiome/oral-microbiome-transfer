#!/usr/bin/env python
"""Experiment #4 - Per-population sign adaptation: how many local labels does it
take to re-orient a global model to a population whose marker directions differ?

Trigger: experiment #3 showed that dropping the sign-reversing genera de-inverts
South Africa but costs accuracy, because it throws away real (if flipped) signal.
The better move is to ADAPT the directions to the target population rather than
discard them. Pure unsupervised sign correction is impossible - you cannot know a
population is flipped without some labels - so the honest question is few-shot:
with k labeled target samples, can we re-orient the global model and recover the
within-cohort signal a pooled model reads backwards?

Model. Interpretable logistic regression in the 139-genus rank space, where a
coefficient's SIGN is exactly a marker's diabetes direction. A global model is fit
on the NHANES+China pool (beta_global). For a target population we fit a
prior-regularized logistic on k local samples:
    minimize  logloss(beta, b; X_cal, y_cal)  +  (lambda/2) * ||beta - beta_global||^2
At k=0 this is the global model (pure transfer); as k grows, coefficients can flip
sign where the population demands it, shrunk toward the global prior to stay stable.

Leakage guard. Within each cohort we use repeated stratified 5-fold CV: the test
fold is held out, the calibration set of size k is drawn from the OTHER folds, and
the global model never saw the cohort. AUC is averaged over folds and seeds. We also
report the within-cohort ceiling (full local CV) and count how many coefficient
signs flip at each k (evidence that adaptation is sign re-orientation, not just
magnitude tuning). `experiment_sign_adaptation.py`.

Reading the output: the per-cohort `reversed` flag means "this LOGISTIC PROBE's k=0
transfer is below 0.5" - it describes the interpretable probe, not the flagship
CatBoost. Portugal carries reversed=true here (logistic 0.483) while its CatBoost
transfer is 0.698; do not read the flag as "the cohort reverses" (2026-09-06 audit).
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "sign_adaptation.json"

LAM = 2.0                      # prior strength (shrink toward the global directions)
KGRID = [0, 5, 10, 20, 40]     # local labels available for calibration
SEEDS = list(range(12))        # repeats to stabilize small-cohort AUC

EXTERNAL = {
    "Portugal":     None,      # from the pkl holdout
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}


def rank_external(counts_path, labels_path, feats):
    c = pd.read_csv(ROOT / counts_path, index_col=0)
    lab = pd.read_csv(ROOT / labels_path, sep="\t", header=None)
    lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
    common = [s for s in c.index if s in lab.index and lab.loc[s] in (0, 1)]
    y = lab.loc[common].astype(int).values
    X = c.loc[common].reindex(columns=feats, fill_value=0).astype(float) \
         .apply(lambda x: pd.Series(rankdata(x, method="average") / len(x), index=feats), axis=1).values
    return X, y


def fit_prior_logistic(X, y, beta0, b0, lam):
    """Logistic regression shrunk toward a prior coefficient vector beta0."""
    n, d = X.shape
    y = y.astype(float)

    def obj(w):
        beta, b = w[:d], w[d]
        z = X @ beta + b
        p = expit(z)
        eps = 1e-9
        ll = -np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
        reg = 0.5 * lam * np.sum((beta - beta0) ** 2)
        g_beta = X.T @ (p - y) + lam * (beta - beta0)
        g_b = np.sum(p - y)
        return ll + reg, np.concatenate([g_beta, [g_b]])

    w0 = np.concatenate([beta0, [b0]])
    res = minimize(obj, w0, jac=True, method="L-BFGS-B", options={"maxiter": 200})
    return res.x[:d], res.x[d]


def within_ceiling(X, y):
    if len(y) < 20 or y.sum() < 5 or (y == 0).sum() < 5:
        return None
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    pr = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        m = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000).fit(X[tr], y[tr])
        pr[te] = m.predict_proba(X[te])[:, 1]
    return round(float(roc_auc_score(y, pr)), 3)


def main():
    d = load_data()
    feats = list(d["feature_names"])
    Xtr, ytr = np.asarray(d["X_train"], dtype=float), np.asarray(d["y_train"])

    from transfer_contract import external_rows, training_for_target, scope

    cohorts = {"Portugal": (np.asarray(d["X_holdout"], dtype=float), np.asarray(d["y_holdout"]))}
    for name, paths in EXTERNAL.items():
        if paths:
            cohorts[name] = external_rows(d, name, *paths)

    results = []
    for name, (X, y) in cohorts.items():
        source_X, source_y = training_for_target(d, name)
        gmodel = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000).fit(source_X, source_y)
        beta_g, b_g = gmodel.coef_.ravel(), float(gmodel.intercept_[0])
        ceiling = within_ceiling(X, y)
        transfer0 = round(float(roc_auc_score(y, gmodel.predict_proba(X)[:, 1])), 3)
        curve = []
        flips_at = {}
        for k in KGRID:
            aucs, flipcounts = [], []
            for seed in SEEDS:
                skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
                pr, yy = [], []
                for tr, te in skf.split(X, y):
                    if k == 0:
                        p = gmodel.predict_proba(X[te])[:, 1]
                        beta = beta_g
                    else:
                        # draw a stratified calibration set of size ~k from the train fold
                        rng = np.random.RandomState(seed * 100 + len(te))
                        idx = _stratified_take(y[tr], k, rng)
                        cal = tr[idx]
                        if y[cal].sum() < 1 or (y[cal] == 0).sum() < 1:
                            p = gmodel.predict_proba(X[te])[:, 1]
                            beta = beta_g
                        else:
                            beta, b = fit_prior_logistic(X[cal], y[cal], beta_g, b_g, LAM)
                            p = expit(X[te] @ beta + b)
                    pr.extend(p); yy.extend(y[te])
                    flipcounts.append(int(np.sum(np.sign(beta) != np.sign(beta_g))))
                if len(set(yy)) == 2:
                    aucs.append(roc_auc_score(yy, pr))
            curve.append({"k": k, "auc": round(float(np.mean(aucs)), 3),
                          "sd": round(float(np.std(aucs)), 3)})
            flips_at[k] = int(np.median(flipcounts)) if flipcounts else 0
        # smallest k that clears chance
        deinvert_k = next((c["k"] for c in curve if c["auc"] >= 0.5), None)
        results.append({"cohort": name, "training_scope": scope(d, name), "n": int(len(y)),
                        "transfer": transfer0, "ceiling": ceiling,
                        "curve": curve, "sign_flips": flips_at,
                        "deinvert_k": deinvert_k,
                        "reversed": transfer0 < 0.5})

    out = {
        "params": {"lambda": LAM, "k_grid": KGRID, "seeds": len(SEEDS),
                   "model": "prior-regularized logistic in 139-genus rank space"},
        "cohorts": results,
        "summary": {
            "sa_transfer": next(r["transfer"] for r in results if r["cohort"] == "South Africa"),
            "sa_ceiling": next(r["ceiling"] for r in results if r["cohort"] == "South Africa"),
            "sa_deinvert_k": next(r["deinvert_k"] for r in results if r["cohort"] == "South Africa"),
            "sa_auc_at_max_k": next(r["curve"][-1]["auc"] for r in results if r["cohort"] == "South Africa"),
        },
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"global logistic transfer (k=0) then few-shot calibration (lambda={LAM}):")
    hdr = "  ".join(f"k={k}" for k in KGRID)
    print(f"  {'cohort':14s} {'n':>4s} {'ceil':>5s}  {hdr}   deinvert@")
    for r in results:
        row = "  ".join(f"{c['auc']:.3f}" for c in r["curve"])
        print(f"  {r['cohort']:14s} {r['n']:4d} {str(r['ceiling']):>5s}  {row}   "
              f"{'k=' + str(r['deinvert_k']) if r['deinvert_k'] is not None else 'never'}")
    print("\nSouth Africa sign flips vs global, by k:",
          next(r["sign_flips"] for r in results if r["cohort"] == "South Africa"))


def _stratified_take(y, k, rng):
    """Indices (into y) of a stratified subsample of total size ~k."""
    pos = np.where(y == 1)[0]; neg = np.where(y == 0)[0]
    kp = max(1, int(round(k * len(pos) / len(y))))
    kn = max(1, k - kp)
    kp = min(kp, len(pos)); kn = min(kn, len(neg))
    return np.concatenate([rng.choice(pos, kp, replace=False),
                           rng.choice(neg, kn, replace=False)])


if __name__ == "__main__":
    main()
