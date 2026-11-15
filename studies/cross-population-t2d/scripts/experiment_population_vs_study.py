#!/usr/bin/env python
"""Experiment #8 - Is the reversal population biology or a study/batch effect?

Trigger: every prior experiment brackets the South Africa reversal but none says
whether it reflects African population biology or a study-specific artifact. The
obvious resolver is a second African cohort (external, unavailable), but there is
a desk-feasible proxy: the training pool contains FOUR Chinese sub-studies (anhui,
shandong, sichuan, shanghai) - same population, different labs/runs. If genus
directions flip among same-population studies about as much as they flip across
populations, then study/batch alone is enough to reverse signs and the "population
biology" reading weakens. If same-population studies agree while populations
disagree, the instability is genuinely population-driven.

Method: per-genus point-biserial T2D association (rank vs label) computed within
each group. Two comparisons:
  - association-vector correlation between group pairs (as in the 2026-08-27
    train-vs-SA analysis): mean over WITHIN-China study pairs vs over
    CROSS-population pairs.
  - sign-flip rate: among genera informative (|r|>=0.15) in >=2 groups, the
    fraction that reverse sign, computed within China vs across populations.
Plus an Atopobium spotlight: does the flagship flipper flip WITHIN China too, or
only across populations? `experiment_population_vs_study.py`.
"""
import json
from itertools import combinations
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata, pointbiserialr, pearsonr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "population_vs_study.json"
R_INFORM = 0.15

EXTERNAL = {
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}


def assoc(X, y):
    y = np.asarray(y); out = np.full(X.shape[1], np.nan)
    for j in range(X.shape[1]):
        col = X[:, j]
        if np.std(col) > 0 and y.sum() > 0 and (y == 0).sum() > 0:
            out[j] = pointbiserialr(y, col).correlation
    return out


def rank_external(cp, lp, feats):
    c = pd.read_csv(ROOT / cp, index_col=0)
    lab = pd.read_csv(ROOT / lp, sep="\t", header=None); lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
    common = [s for s in c.index if s in lab.index and lab.loc[s] in (0, 1)]
    X = c.loc[common].reindex(columns=feats, fill_value=0).astype(float) \
         .apply(lambda x: pd.Series(rankdata(x, method="average") / len(x), index=feats), axis=1).values
    return X, lab.loc[common].astype(int).values


def vec_corr(a, b):
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 20:
        return None
    return float(pearsonr(a[m], b[m])[0])


def flip_rate(vectors):
    """Among genera informative (|r|>=R_INFORM) in >=2 of the given assoc vectors,
    fraction that carry both a + and a - sign."""
    A = np.vstack(vectors).T
    flip = tot = 0
    for i in range(A.shape[0]):
        r = A[i]; inf = r[~np.isnan(r) & (np.abs(r) >= R_INFORM)]
        if len(inf) >= 2:
            tot += 1
            if (inf > 0).any() and (inf < 0).any():
                flip += 1
    return (round(flip / tot, 2) if tot else None, tot)


def main():
    d = load_data()
    feats = list(d["feature_names"])
    sl = np.asarray(d["study_labels"]); Xtr = np.asarray(d["X_train"], float); ytr = np.asarray(d["y_train"])

    # per-genus association within each Chinese sub-study (same population, diff studies)
    china_studies = sorted({s for s in sl if s.startswith("china")})
    china_assoc = {s: assoc(Xtr[sl == s], ytr[sl == s]) for s in china_studies}

    # per-genus association per distinct POPULATION
    pop_assoc = {
        "NHANES (US)": assoc(Xtr[sl == "nhanes"], ytr[sl == "nhanes"]),
        "China": assoc(Xtr[np.array([s.startswith("china") for s in sl])],
                       ytr[np.array([s.startswith("china") for s in sl])]),
        "Portugal": assoc(np.asarray(d["X_holdout"], float), np.asarray(d["y_holdout"])),
    }
    for name, (cp, lp) in EXTERNAL.items():
        X, y = rank_external(cp, lp, feats); pop_assoc[name] = assoc(X, y)

    # comparison 1: association-vector correlation, within-China pairs vs cross-population pairs
    within = [vec_corr(china_assoc[a], china_assoc[b]) for a, b in combinations(china_studies, 2)]
    within = [c for c in within if c is not None]
    cross = [vec_corr(pop_assoc[a], pop_assoc[b]) for a, b in combinations(pop_assoc, 2)]
    cross = [c for c in cross if c is not None]

    # comparison 2: sign-flip rate within China vs across populations
    within_flip, within_n = flip_rate(list(china_assoc.values()))
    cross_flip, cross_n = flip_rate(list(pop_assoc.values()))

    # Atopobium spotlight
    ai = feats.index("Atopobium") if "Atopobium" in feats else None
    atop = {"china_by_study": {s: (None if np.isnan(china_assoc[s][ai]) else round(float(china_assoc[s][ai]), 3)) for s in china_studies} if ai is not None else {},
            "by_population": {p: (None if np.isnan(pop_assoc[p][ai]) else round(float(pop_assoc[p][ai]), 3)) for p in pop_assoc} if ai is not None else {}}

    out = {
        "params": {"r_inform": R_INFORM},
        "china_studies": china_studies,
        "populations": list(pop_assoc.keys()),
        "assoc_vector_correlation": {
            "within_china_mean": round(float(np.mean(within)), 3), "within_china_pairs": len(within),
            "cross_population_mean": round(float(np.mean(cross)), 3), "cross_population_pairs": len(cross),
            "within_china_values": [round(c, 3) for c in within],
        },
        "sign_flip_rate": {
            "within_china": within_flip, "within_china_n": within_n,
            "cross_population": cross_flip, "cross_population_n": cross_n,
        },
        "atopobium": atop,
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    c = out["assoc_vector_correlation"]
    print("Association-vector correlation (higher = directions agree):")
    print(f"  within-China (same population, {c['within_china_pairs']} study pairs): mean r = {c['within_china_mean']}")
    print(f"  cross-population ({c['cross_population_pairs']} pairs):                  mean r = {c['cross_population_mean']}")
    f = out["sign_flip_rate"]
    print("Sign-flip rate (fraction of informative genera reversing):")
    print(f"  within-China:     {f['within_china']}  (of {f['within_china_n']} genera)")
    print(f"  cross-population:  {f['cross_population']}  (of {f['cross_population_n']} genera)")
    print("Atopobium association:")
    print(f"  within China by study: {atop['china_by_study']}")
    print(f"  by population:         {atop['by_population']}")


if __name__ == "__main__":
    main()
