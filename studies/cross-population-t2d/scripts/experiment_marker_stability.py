#!/usr/bin/env python
"""Experiment #2 - Cross-population marker stability.

Trigger: the South Africa reversal showed Atopobium flips its T2D association
sign (control-associated in the training populations, case-associated in SA).
That convicts a systematic question: across ALL six populations, which oral
genera keep a consistent direction (trustworthy markers) and which flip
(population-specific)? A model can only transfer on the stable ones.

Method (leakage-free, matches the flagship pipeline):
  - Six populations in the shared 139-genus space: NHANES (US) and China come
    from the training pool (split by study_labels); Portugal is the geographic
    holdout; India/Mumbai, Mexico, South Africa are the external cohorts, each
    per-sample rank-transformed (rankdata(x)/len(x)) exactly as at inference.
  - Per genus per cohort: point-biserial correlation between the sample's rank
    for that genus and the T2D label. Sign = direction, |r| = strength.
  - A genus is "informative" in a cohort when it is present/variable there
    (rank std > 0) and |r| >= R_INFORM. Classify each genus:
      robust_up / robust_down : informative in >= MIN_ROBUST cohorts, one sign only
      flipper                 : >= +R_FLIP in one cohort and <= -R_FLIP in another
      weak                    : never clears R_INFORM

Output: data/processed/marker_panel.json (consumed by build_site_data.py) plus a
graded stdout report. Confidence is stated, not implied: these are associations
in modest per-cohort samples, not causal or diagnostic claims.

  .venv/bin/python scripts/experiment_marker_stability.py
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata, pointbiserialr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "marker_panel.json"

# Stability is defined by DIRECTION consistency, not magnitude. A fixed |r| gate
# is the wrong tool here: NHANES (n=9683) has a diffuse signal (median |r|=0.01),
# so any magnitude threshold makes the largest cohort look "uninformative" and
# sinks the metric. So a cohort casts a *sign vote* once |r| clears a small noise
# floor (R_VOTE); a genus is robust when its sign agrees across almost every cohort.
R_VOTE = 0.05      # |r| floor for a cohort's sign to count (filters pure noise)
R_INFORM = 0.15    # |r| for the flip-prevalence tally (a clear, non-trivial effect)
R_FLIP = 0.15      # |r| in BOTH directions across cohorts => flipper
MIN_VOTES = 5      # sign votes in >= this many cohorts (of 6) to be eligible robust
AGREE_ROBUST = 0.8 # fraction of voting cohorts that must share the sign

EXTERNAL = {
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv", "South Asian"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv",      "Latin American"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv", "African"),
}
# display order = the map's west-to-east narrative, training pops first
ORDER = ["NHANES (US)", "China", "Portugal", "India/Mumbai", "Mexico", "South Africa"]
POP = {"NHANES (US)": "US", "China": "Chinese", "Portugal": "European"}


def rank_external(counts_path, labels_path, feats):
    c = pd.read_csv(ROOT / counts_path, index_col=0)
    lab = pd.read_csv(ROOT / labels_path, sep="\t", header=None)
    lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
    common = [s for s in c.index if s in lab.index and lab.loc[s] in (0, 1)]
    y = lab.loc[common].astype(int).values
    X = c.loc[common].reindex(columns=feats, fill_value=0).astype(float) \
         .apply(lambda x: pd.Series(rankdata(x, method="average") / len(x), index=feats), axis=1).values
    return X, y


def assoc(X, y):
    """Signed point-biserial r per feature; nan where the feature has no variance."""
    y = np.asarray(y)
    out = np.zeros(X.shape[1])
    for j in range(X.shape[1]):
        col = X[:, j]
        if np.std(col) == 0 or y.sum() == 0 or (y == 0).sum() == 0:
            out[j] = np.nan
        else:
            out[j] = pointbiserialr(y, col).correlation
    return out


def main():
    d = load_data()
    feats = list(d["feature_names"])
    sl = np.asarray(d["study_labels"])
    Xtr, ytr = np.asarray(d["X_train"], dtype=float), np.asarray(d["y_train"])

    cohorts = {}  # name -> (X, y, population)
    cohorts["NHANES (US)"] = (Xtr[sl == "nhanes"], ytr[sl == "nhanes"], "US")
    chi = np.array([s.startswith("china") for s in sl])
    cohorts["China"] = (Xtr[chi], ytr[chi], "Chinese")
    cohorts["Portugal"] = (np.asarray(d["X_holdout"], dtype=float), np.asarray(d["y_holdout"]), "European")
    for name, (cp, lp, pop) in EXTERNAL.items():
        X, y = rank_external(cp, lp, feats)
        cohorts[name] = (X, y, pop)

    names = [n for n in ORDER if n in cohorts]
    meta = [{"name": n, "population": cohorts[n][2], "n": int(len(cohorts[n][1])),
             "cases": int(cohorts[n][1].sum()), "controls": int((cohorts[n][1] == 0).sum())} for n in names]

    # association matrix: genus x cohort
    A = np.vstack([assoc(cohorts[n][0], cohorts[n][1]) for n in names]).T  # (139, 6)

    genera = []
    for i, g in enumerate(feats):
        r = A[i]
        present = ~np.isnan(r)
        if present.sum() < 2:
            continue
        rp = r[present]
        votes = rp[np.abs(rp) >= R_VOTE]                 # cohorts whose sign counts
        n_votes = int(len(votes))
        vote_mean = float(votes.mean()) if n_votes else 0.0
        agree = float(np.mean(np.sign(votes) == np.sign(vote_mean))) if n_votes else 0.0
        has_up = (rp >= R_FLIP).any()
        has_down = (rp <= -R_FLIP).any()
        if has_up and has_down:
            klass = "flipper"
        elif n_votes >= MIN_VOTES and agree >= AGREE_ROBUST:
            klass = "robust_up" if vote_mean > 0 else "robust_down"
        else:
            klass = "weak"
        mean_r = float(np.nanmean(r))
        genera.append({
            "genus": g,
            "r": [None if np.isnan(v) else round(float(v), 3) for v in r],
            "mean_r": round(mean_r, 3),
            "abs_mean_r": round(abs(mean_r), 3),
            "n_present": int(present.sum()),
            "n_votes": n_votes,
            "agreement": round(agree, 2),
            "spread": round(float(rp.max() - rp.min()), 3),
            "class": klass,
        })

    robust_up = sorted([g for g in genera if g["class"] == "robust_up"],
                       key=lambda g: (-g["agreement"], -g["abs_mean_r"]))
    robust_down = sorted([g for g in genera if g["class"] == "robust_down"],
                         key=lambda g: (-g["agreement"], -g["abs_mean_r"]))
    flippers = sorted([g for g in genera if g["class"] == "flipper"], key=lambda g: -g["spread"])

    # Effect: how do the pooled model's strongest training markers behave in SA
    # vs the other test cohorts? ties the panel back to the reversal.
    sa_i = names.index("South Africa")
    train_markers = sorted(range(len(feats)), key=lambda i: -abs(np.nanmean(A[i, :2])))[:20]  # top by |r| in NHANES+China
    def flip_frac(ci):
        f = 0; tot = 0
        for i in train_markers:
            base = np.nanmean(A[i, :2]); cur = A[i, ci]
            if np.isnan(base) or np.isnan(cur) or abs(base) < R_INFORM:
                continue
            tot += 1
            if np.sign(base) != np.sign(cur) and abs(cur) >= 0.1:
                f += 1
        return (round(f / tot, 2) if tot else None, tot)
    sa_flip, sa_tot = flip_frac(sa_i)
    other_flip = {names[ci]: flip_frac(ci)[0] for ci in range(len(names)) if names[ci] not in ("NHANES (US)", "China", "South Africa")}

    # Artifact-free reversal prevalence: among genera informative (|r|>=R_INFORM) in
    # >=2 cohorts EXCLUDING NHANES (whose magnitudes are not comparable), what
    # fraction reverse sign? This is the headline and does not depend on NHANES.
    ex = [ci for ci in range(len(names)) if names[ci] != "NHANES (US)"]
    n_flip = n_tot = 0
    for g in genera:
        rr = [g["r"][ci] for ci in ex if g["r"][ci] is not None and abs(g["r"][ci]) >= R_INFORM]
        if len(rr) >= 2:
            n_tot += 1
            if any(v > 0 for v in rr) and any(v < 0 for v in rr):
                n_flip += 1
    reversal_prev = round(n_flip / n_tot, 2) if n_tot else None

    # Curated heatmap for the dashboard: the robust panel then the sharpest flippers.
    hm_order = robust_up[:6] + robust_down[:6] + flippers[:14]
    seen, heatmap = set(), []
    for g in hm_order:
        if g["genus"] in seen:
            continue
        seen.add(g["genus"])
        heatmap.append({"genus": g["genus"], "r": g["r"], "class": g["class"],
                        "agreement": g["agreement"], "mean_r": g["mean_r"]})

    panel = {
        "params": {"r_vote": R_VOTE, "r_inform": R_INFORM, "r_flip": R_FLIP,
                   "min_votes": MIN_VOTES, "agree_robust": AGREE_ROBUST},
        "cohorts": names,
        "cohort_meta": meta,
        "genera": sorted(genera, key=lambda g: -g["abs_mean_r"]),
        "heatmap": heatmap,
        "robust_up": [g["genus"] for g in robust_up],
        "robust_down": [g["genus"] for g in robust_down],
        "flippers": [g["genus"] for g in flippers],
        "summary": {
            "n_genera_evaluated": len(genera),
            "n_robust": len(robust_up) + len(robust_down),
            "n_flippers": len(flippers),
            "reversal_prevalence_ex_nhanes": reversal_prev,
            "reversal_tested_ex_nhanes": n_tot,
            "sa_marker_flip_fraction": sa_flip,
            "sa_markers_tested": sa_tot,
            "other_cohort_flip_fraction": other_flip,
        },
    }
    panel["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(panel, indent=2) + "\n")

    # graded report
    cohort_str = ", ".join("{}(n={})".format(m["name"], m["n"]) for m in meta)
    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"cohorts: {cohort_str}")
    print(f"evaluated {len(genera)} genera | robust {panel['summary']['n_robust']} "
          f"({len(robust_up)} up, {len(robust_down)} down) | flippers {len(flippers)}")
    print(f"reversal prevalence (excl NHANES): {reversal_prev} of {n_tot} genera informative in >=2 populations")
    print(f"\nTop robust CASE-associated (direction stable across populations):")
    for g in robust_up[:8]:
        print(f"  +{g['mean_r']:.2f}  {g['genus']:22s} agree {g['agreement']:.2f}, votes {g['n_votes']}/{len(names)}")
    print(f"Top robust CONTROL-associated:")
    for g in robust_down[:8]:
        print(f"  {g['mean_r']:.2f}  {g['genus']:22s} agree {g['agreement']:.2f}, votes {g['n_votes']}/{len(names)}")
    print(f"\nFlippers (sign reverses across populations):")
    for g in flippers[:10]:
        cells = ", ".join(f"{names[k].split()[0]}={g['r'][k]:+.2f}" for k in range(len(names)) if g['r'][k] is not None and abs(g['r'][k]) >= R_INFORM)
        print(f"  {g['genus']:22s} {cells}")
    print(f"\nEffect - pooled model's top-20 training markers, sign-flip fraction by cohort:")
    print(f"  South Africa: {sa_flip} of {sa_tot} tested")
    for k, v in other_flip.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
