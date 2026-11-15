#!/usr/bin/env python
"""Experiment #5 - Can the model know it is about to fail, without labels?

Trigger: experiment #4 re-orients a reversed population, but only with local
labels. The open question is detection, not correction: before any labels, can a
deployment tell that a new population is out-of-distribution (OOD) and likely to
be read backwards, so it flags/refuses instead of being confidently wrong?

Method (fully unsupervised w.r.t. the target's diabetes labels): reference = the
pooled training distribution in the 139-genus rank space. For each unseen cohort
compute two label-free OOD scores:
  - domain-classifier AUC: a classifier's 5-fold CV AUC separating training
    samples from the cohort's samples (balanced downsample of training to the
    cohort size, averaged over seeds). ~0.5 = indistinguishable (in-distribution),
    ~1.0 = easily separable (OOD). This is a classifier two-sample test.
  - centroid Mahalanobis distance from the training distribution (Ledoit-Wolf
    shrinkage covariance).
Then ask whether either score, computed with NO diabetes labels, ranks cohorts by
transfer failure and specifically flags the reversed one (South Africa).

Honest framing: only four unseen cohorts, so any OOD-vs-transfer correlation is
weak; the useful question is qualitative - does OOD separate the reversed cohort
from the ones that transfer, or is being different indistinguishable from being
backwards? `experiment_ood_detection.py`.
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.covariance import LedoitWolf
from transfer_contract import external_rows, training_for_target, scope
from reconstruct_validation import model as catboost_model, auc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "ood_detection.json"

# transfer AUCs from the flagship leaderboard (the outcome OOD is meant to predict)
EXTERNAL = {
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}
SEEDS = list(range(15))


def rank_external(counts_path, labels_path, feats):
    c = pd.read_csv(ROOT / counts_path, index_col=0)
    lab = pd.read_csv(ROOT / labels_path, sep="\t", header=None)
    lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
    common = [s for s in c.index if s in lab.index and lab.loc[s] in (0, 1)]
    X = c.loc[common].reindex(columns=feats, fill_value=0).astype(float) \
         .apply(lambda x: pd.Series(rankdata(x, method="average") / len(x), index=feats), axis=1).values
    return X


def domain_auc(Xtrain, Xcohort, seeds=SEEDS):
    """5-fold CV AUC separating training from cohort, on a balanced downsample."""
    n = len(Xcohort)
    aucs = []
    for s in seeds:
        rng = np.random.RandomState(s)
        idx = rng.choice(len(Xtrain), n, replace=False)
        X = np.vstack([Xtrain[idx], Xcohort])
        y = np.r_[np.zeros(n), np.ones(n)]
        skf = StratifiedKFold(5, shuffle=True, random_state=s)
        oof = np.zeros(len(y))
        for tr, te in skf.split(X, y):
            m = LogisticRegression(C=1.0, max_iter=1000).fit(X[tr], y[tr])
            oof[te] = m.predict_proba(X[te])[:, 1]
        aucs.append(roc_auc_score(y, oof))
    return round(float(np.mean(aucs)), 3)


def main():
    d = load_data()
    feats = list(d["feature_names"])
    Xtr = np.asarray(d["X_train"], float)

    cohorts = {"Portugal": (np.asarray(d["X_holdout"], float), np.asarray(d["y_holdout"]))}
    for name, (cp, lp) in EXTERNAL.items():
        cohorts[name] = external_rows(d, name, cp, lp)
    full = catboost_model().fit(Xtr, np.asarray(d["y_train"]))

    rows = []
    for name, (X, y) in cohorts.items():
        source_X, source_y = training_for_target(d, name)
        reference = catboost_model().fit(source_X, source_y) if name == "India/Mumbai" else full
        transfer = round(auc(y, reference.predict_proba(X)[:, 1]), 3)
        lw = LedoitWolf().fit(source_X)
        mu = source_X.mean(0)
        dauc = domain_auc(source_X, X)
        maha = float(np.sqrt((X.mean(0) - mu) @ lw.precision_ @ (X.mean(0) - mu)))
        rows.append({"cohort": name, "training_scope": scope(d, name), "n": int(len(X)), "transfer": transfer,
                     "reversed": transfer < 0.5, "domain_auc": dauc,
                     "mahalanobis": round(maha, 2)})

    # do the label-free OOD scores rank cohorts by transfer failure?
    order = sorted(rows, key=lambda r: -r["domain_auc"])
    t = np.array([r["transfer"] for r in rows]); da = np.array([r["domain_auc"] for r in rows])
    rho = spearmanr(da, t).correlation
    most_ood = max(rows, key=lambda r: r["domain_auc"])
    rev = next(r for r in rows if r["reversed"])
    # can OOD tell the reversed cohort apart from the best-transferring one?
    best = max(rows, key=lambda r: r["transfer"])
    sep = rev["domain_auc"] - best["domain_auc"]

    out = {
        "params": {"reference": "pooled training (NHANES+China) 139-genus rank space",
                   "scores": "domain-classifier AUC + centroid Mahalanobis", "seeds": len(SEEDS)},
        "cohorts": rows,
        "analysis": {
            "spearman_ood_vs_transfer": None if rho is None else round(float(rho), 3),
            "most_ood_cohort": most_ood["cohort"],
            "reversed_cohort": rev["cohort"],
            "reversed_is_most_ood": most_ood["cohort"] == rev["cohort"],
            "ood_gap_reversed_minus_best": round(sep, 3),
        },
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"  {'cohort':14s} {'n':>4s} {'transfer':>8s} {'domainAUC':>9s} {'maha':>7s}")
    for r in sorted(rows, key=lambda r: -r["domain_auc"]):
        flag = "  <- reversed" if r["reversed"] else ""
        print(f"  {r['cohort']:14s} {r['n']:4d} {r['transfer']:8.3f} {r['domain_auc']:9.3f} {r['mahalanobis']:7.2f}{flag}")
    a = out["analysis"]
    print(f"\n  Spearman(OOD, transfer) over {len(rows)} cohorts: {a['spearman_ood_vs_transfer']} (weak: n=4)")
    print(f"  most OOD: {a['most_ood_cohort']} | reversed: {a['reversed_cohort']} | "
          f"reversed is most OOD? {a['reversed_is_most_ood']}")
    print(f"  OOD gap (reversed - best-transfer): {a['ood_gap_reversed_minus_best']:+.3f}")


if __name__ == "__main__":
    main()
