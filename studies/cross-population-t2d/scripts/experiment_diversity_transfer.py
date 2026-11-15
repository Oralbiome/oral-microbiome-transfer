#!/usr/bin/env python
"""Experiment #7 - Does coarse community diversity transfer where specific taxa don't?

Trigger: experiments #2-#6 show the taxonomic signal is real but direction-unstable
across populations. A natural question is whether a coarser summary of the
community, its alpha diversity, carries a T2D signal that is weaker but more
portable, because a single scalar is less sensitive to which specific genera flip.

Method: over the 139 model genera (a shared reference across all cohorts) compute
per-sample Shannon, Simpson, and richness from raw counts. Training pool and the
Portugal holdout come from the unified raw-count table joined to the pkl's
sample-id labels; India/Mumbai, Mexico, and South Africa come from their interim
count tables + recovered labels. A logistic model on the three diversity features
is trained on the pooled training data and (a) cross-validated within each cohort
and (b) transferred to each unseen cohort, then compared to the 139-genus
taxonomic model. We also report the direction of Shannon diversity (T2D minus
control) per cohort, to see whether diversity reverses like the taxa do.
`experiment_diversity_transfer.py`.
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "diversity_transfer.json"

from transfer_contract import external_rows, training_mask, training_for_target, scope
from reconstruct_validation import model as catboost_model, auc
EXTERNAL = {
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}


def diversity(counts):
    """rows = samples, cols = the 139 genera (raw counts) -> shannon/simpson/richness."""
    C = counts.values.astype(float)
    tot = C.sum(1, keepdims=True); tot[tot == 0] = np.nan
    P = C / tot
    with np.errstate(divide="ignore", invalid="ignore"):
        shannon = -np.nansum(np.where(P > 0, P * np.log(P), 0.0), axis=1)
    simpson = 1 - np.nansum(P ** 2, axis=1)
    richness = (C > 0).sum(1)
    return pd.DataFrame({"shannon": shannon, "simpson": simpson, "richness": richness}, index=counts.index)


def model():
    return make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000))


def within(D, y):
    if len(y) < 20 or y.sum() < 5 or (y == 0).sum() < 5:
        return None
    skf = StratifiedKFold(5, shuffle=True, random_state=0)
    oof = cross_val_predict(model(), D, y, cv=skf, method="predict_proba")[:, 1]
    return round(float(roc_auc_score(y, oof)), 3)


def main():
    d = load_data()
    feats = list(d["feature_names"])
    uni = pd.read_csv(ROOT / "data/processed/unified_genus_counts.csv", index_col=0, low_memory=False)
    uni.index = uni.index.astype(str)
    uni = uni.apply(pd.to_numeric, errors="coerce").fillna(0)

    def counts_for(df_index):
        ids = [s for s in df_index.astype(str) if s in uni.index]
        return uni.loc[ids, feats], ids

    # training pool + Portugal from unified (joined by sample id), labels from the pkl
    tr_counts, tr_ids = counts_for(d["X_train_df"].index)
    ytr = pd.Series(np.asarray(d["y_train"]), index=d["X_train_df"].index.astype(str)).loc[tr_ids].values
    Dtr = diversity(tr_counts)

    cohorts = {}
    ph_counts, ph_ids = counts_for(d["X_holdout_df"].index)
    yph = pd.Series(np.asarray(d["y_holdout"]), index=d["X_holdout_df"].index.astype(str)).loc[ph_ids].values
    cohorts["Portugal"] = (diversity(ph_counts), yph)
    for name, (cp, lp) in EXTERNAL.items():
        c = pd.read_csv(ROOT / cp, index_col=0)
        lab = pd.read_csv(ROOT / lp, sep="\t", header=None); lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
        common = [s for s in c.index if s in lab.index and lab.loc[s] in (0, 1)]
        C = c.loc[common].reindex(columns=feats, fill_value=0)
        cohorts[name] = (diversity(C), lab.loc[common].astype(int).values)

    gm = model().fit(Dtr, ytr)
    flagship = catboost_model().fit(np.asarray(d["X_train"]), np.asarray(d["y_train"]))

    rows = []
    for name, (D, y) in cohorts.items():
        source_X, source_y = training_for_target(d, name)
        if name == "India/Mumbai":
            kept_ids = set(map(str, np.asarray(d["study_labels"].index)[training_mask(d, name)]))
            keep = np.array([str(i) in kept_ids for i in tr_ids])
            diversity_model = model().fit(Dtr.iloc[np.flatnonzero(keep)], ytr[keep])
            taxa_model = catboost_model().fit(source_X, source_y)
        else:
            diversity_model, taxa_model = gm, flagship
        if name == "Portugal":
            taxa_X = np.asarray(d["X_holdout"])
        else:
            taxa_X, checked_y = external_rows(d, name, *EXTERNAL[name])
            assert np.array_equal(y, checked_y)
        taxa_transfer = round(auc(y, taxa_model.predict_proba(taxa_X)[:, 1]), 3)
        transfer = round(float(roc_auc_score(y, diversity_model.predict_proba(D)[:, 1])), 3)
        wl = within(D, y)
        # direction of Shannon: mean(T2D) - mean(control)
        sh = D["shannon"].values
        sdir = round(float(sh[y == 1].mean() - sh[y == 0].mean()), 3)
        rows.append({"cohort": name, "training_scope": scope(d, name), "n": int(len(y)),
                     "diversity_within": wl, "diversity_transfer": transfer,
                     "taxa_transfer": taxa_transfer,
                     "shannon_t2d_minus_ctrl": sdir,
                     "diversity_reversed": transfer < 0.5})

    out = {
        "features": ["shannon", "simpson", "richness"],
        "note": "diversity computed over the 139 model genera (shared reference across cohorts)",
        "training_within_cv": within(Dtr, ytr),
        "cohorts": rows,
        "summary": {
            "mean_diversity_transfer": round(float(np.mean([r["diversity_transfer"] for r in rows])), 3),
            "mean_taxa_transfer": round(float(np.mean([r["taxa_transfer"] for r in rows])), 3),
            "diversity_reversed_cohorts": sum(r["diversity_reversed"] for r in rows),
        },
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"training within-CV (diversity): {out['training_within_cv']}")
    print(f"  {'cohort':14s} {'n':>4s} {'div-within':>10s} {'div-transfer':>12s} {'taxa-transfer':>13s} {'Shannon dir':>12s}")
    for r in rows:
        flag = "  <- div reversed" if r["diversity_reversed"] else ""
        print(f"  {r['cohort']:14s} {r['n']:4d} {str(r['diversity_within']):>10s} {r['diversity_transfer']:12.3f} "
              f"{r['taxa_transfer']:13.3f} {r['shannon_t2d_minus_ctrl']:+12.3f}{flag}")
    s = out["summary"]
    print(f"\nmean transfer: diversity {s['mean_diversity_transfer']} vs taxa {s['mean_taxa_transfer']} | "
          f"diversity reversed in {s['diversity_reversed_cohorts']} cohorts")


if __name__ == "__main__":
    main()
