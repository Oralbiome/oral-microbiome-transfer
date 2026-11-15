#!/usr/bin/env python
"""Experiment #6 - What makes an oral genus a portable T2D marker?

Trigger: experiment #2 split the 139 model genera into direction-stable markers
and sign-reversing flippers, but did not ask WHY a genus lands in one bucket. If
flippers are simply the rare, low-abundance taxa whose association sign is noisy,
then a portable panel should be built from prevalent, abundant genera and the
handful of prevalent-yet-reversing genera (Atopobium) are the biologically
interesting exceptions. That is directly actionable for panel design.

Method: for each of the 139 model genera compute two label-free, intrinsic
properties from the full raw genus-count table (unified_genus_counts.csv):
  - prevalence: fraction of samples where the genus is detected (count > 0)
  - mean relative abundance: mean of count / sample_total across samples
Join with the stability class from experiment #2 (marker_panel.json). Then test
whether stable markers differ from flippers in these properties (Mann-Whitney),
fit a small logistic (flipper ~ log-prevalence + log-abundance) to see which
property carries the signal, and flag the prevalent+abundant flippers, the ones
that reverse for reasons other than sparsity. `experiment_marker_properties.py`.
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "marker_properties.json"


def main():
    d = load_data()
    feats = list(d["feature_names"])

    # intrinsic genus properties from the full raw count table
    counts = pd.read_csv(ROOT / "data/processed/unified_genus_counts.csv", index_col=0, low_memory=False)
    counts.index = counts.index.astype(str)
    source_ids = d['X_train_df'].index.astype(str)
    if not source_ids.isin(counts.index).all():
        raise ValueError('Audited source rows missing from genus counts')
    counts = counts.loc[source_ids]
    counts = counts.apply(pd.to_numeric, errors="coerce").fillna(0)
    totals = counts.sum(axis=1).replace(0, np.nan)
    rel = counts[feats].div(totals, axis=0)
    prevalence = (counts[feats] > 0).mean(axis=0)          # fraction of samples detected
    abundance = rel.mean(axis=0)                            # mean relative abundance

    # stability from experiment #2
    panel = json.loads((ROOT / "data/processed/marker_panel.json").read_text())
    cls = {g["genus"]: g for g in panel["genera"]}

    rows = []
    for g in feats:
        c = cls.get(g)
        if not c:
            continue
        rows.append({
            "genus": g,
            "prevalence": round(float(prevalence[g]), 4),
            "abundance": round(float(abundance[g]), 6),
            "log_prevalence": float(np.log10(prevalence[g] + 1e-4)),
            "log_abundance": float(np.log10(abundance[g] + 1e-7)),
            "class": c["class"],
            "abs_mean_r": c["abs_mean_r"],
            "stable": c["class"] in ("robust_up", "robust_down"),
            "flipper": c["class"] == "flipper",
        })
    df = pd.DataFrame(rows)

    stable = df[df["stable"]]
    flip = df[df["flipper"]]

    def mw(col):
        u, p = mannwhitneyu(stable[col], flip[col], alternative="two-sided")
        return {"stable_median": round(float(stable[col].median()), 4),
                "flipper_median": round(float(flip[col].median()), 4),
                "p": round(float(p), 4)}

    # which property predicts flipper vs stable?
    sub = df[df["stable"] | df["flipper"]].copy()
    X = sub[["log_prevalence", "log_abundance"]].values
    y = sub["flipper"].astype(int).values
    lr = LogisticRegression(max_iter=1000).fit((X - X.mean(0)) / X.std(0), y)
    coef = dict(zip(["log_prevalence", "log_abundance"], lr.coef_.ravel().round(3).tolist()))

    # Common reversers: prevalence alone does not explain the sign instability.
    prev_med, ab_med = df["prevalence"].median(), df["abundance"].median()
    exceptions = flip[(flip["prevalence"] >= prev_med) & (flip["abundance"] >= ab_med)] \
        .sort_values("abs_mean_r", ascending=False)

    out = {
        "n_stable": int(len(stable)), "n_flipper": int(len(flip)),
        "prevalence": mw("prevalence"),
        "abundance": mw("abundance"),
        "flipper_logit_coef_standardized": coef,
        "medians": {"prevalence": round(float(prev_med), 4), "abundance": round(float(ab_med), 6)},
        "prevalent_abundant_flippers": exceptions["genus"].tolist()[:12],
        "genera": [{"genus": r["genus"], "prevalence": r["prevalence"], "abundance": r["abundance"],
                    "class": r["class"], "abs_mean_r": r["abs_mean_r"]} for r in rows],
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"stable={len(stable)}  flippers={len(flip)}")
    print(f"prevalence : stable median {out['prevalence']['stable_median']} vs flipper {out['prevalence']['flipper_median']}  (p={out['prevalence']['p']})")
    print(f"abundance  : stable median {out['abundance']['stable_median']} vs flipper {out['abundance']['flipper_median']}  (p={out['abundance']['p']})")
    print(f"flipper logit (standardized): {coef}  (negative => flippers are lower on that property)")
    print(f"prevalent+abundant flippers (reverse despite being common): {out['prevalent_abundant_flippers']}")


if __name__ == "__main__":
    main()
