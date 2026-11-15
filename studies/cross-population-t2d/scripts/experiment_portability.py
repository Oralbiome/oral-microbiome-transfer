#!/usr/bin/env python
"""Experiment #3 - Portability over accuracy: does restricting to direction-stable
genera reduce cross-population failure?

Trigger: experiment #2 showed the transfer gap is a direction problem (71% of
informative genera flip sign; the model's top markers flip 40-50% in distant
cohorts). The convicted hypothesis: a model built only on direction-stable genera
should transfer more honestly - fewer confident reversals - even if it loses raw
accuracy, because it drops the flippers (Atopobium first) that the pooled model
reads backwards.

Leakage guard: the stable set from experiment #2 was defined using the test
cohorts themselves, so restricting features and then testing on those same cohorts
would be circular. We select leave-one-cohort-out (LOCO): to evaluate transfer to
cohort T, the stable genera are chosen from the OTHER cohorts only, so T's labels
never inform its own feature selection. Training always uses only the NHANES+China
pool (never a test cohort).

Two tests:
  A. LOCO stable-restricted vs full-feature transfer AUC per test cohort.
  B. Mechanism ablation: drop the single dominant marker Atopobium (chosen by
     TRAINING importance alone, leakage-free) and measure South Africa transfer.

Confidence is graded: small per-cohort n, and a de-inversion toward 0.5 is a loss
of confident-wrongness, not a gain of skill. `experiment_portability.py`.
"""
import json
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata, pointbiserialr
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score
from transfer_contract import external_rows, training_for_target, scope

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "portability.json"

R_VOTE = 0.05
AGREE = 0.8        # sign agreement among voting cohorts to call a genus stable
MIN_VOTES = 4      # of the 5 LOCO selection cohorts

EXTERNAL = {
    "India/Mumbai": ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "Mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "South Africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}


def cb():
    return CatBoostClassifier(iterations=200, depth=4, learning_rate=0.1,
                              auto_class_weights="Balanced", random_state=42, verbose=0,
                              allow_writing_files=False, thread_count=4)


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
    y = np.asarray(y)
    out = np.full(X.shape[1], np.nan)
    for j in range(X.shape[1]):
        col = X[:, j]
        if np.std(col) > 0 and y.sum() > 0 and (y == 0).sum() > 0:
            out[j] = pointbiserialr(y, col).correlation
    return out


def stable_mask(assoc_by_cohort, feats):
    """Genera whose sign agrees across >=MIN_VOTES voting cohorts (|r|>=R_VOTE)."""
    A = np.vstack(assoc_by_cohort).T  # (n_feats, n_cohorts)
    keep = np.zeros(len(feats), dtype=bool)
    for i in range(len(feats)):
        r = A[i]
        votes = r[~np.isnan(r) & (np.abs(r) >= R_VOTE)]
        if len(votes) >= MIN_VOTES:
            m = votes.mean()
            if np.mean(np.sign(votes) == np.sign(m)) >= AGREE:
                keep[i] = True
    return keep


def transfer(model, cols, X, y):
    return round(float(roc_auc_score(y, model.predict_proba(X[:, cols])[:, 1])), 3)


def main():
    d = load_data()
    feats = list(d["feature_names"])
    sl = np.asarray(d["study_labels"])
    Xtr, ytr = np.asarray(d["X_train"], dtype=float), np.asarray(d["y_train"])

    # per-cohort rank matrices in the shared space (for association-based selection)
    coh = {
        "NHANES (US)": (Xtr[sl == "nhanes"], ytr[sl == "nhanes"]),
        "China": (Xtr[np.array([s.startswith("china") for s in sl])],
                  ytr[np.array([s.startswith("china") for s in sl])]),
        "Portugal": (np.asarray(d["X_holdout"], dtype=float), np.asarray(d["y_holdout"])),
    }
    for name, (cp, lp) in EXTERNAL.items():
        coh[name] = external_rows(d, name, cp, lp)
    assoc_all = {n: assoc(X, y) for n, (X, y) in coh.items()}

    full = cb().fit(Xtr, ytr)                          # full-feature pooled model
    all_cols = list(range(len(feats)))
    test_cohorts = ["Portugal", "India/Mumbai", "Mexico", "South Africa"]

    # Test A: LOCO stable-restricted vs full
    rows = []
    for T in test_cohorts:
        sel = [n for n in coh if n != T]               # choose stable set from the OTHER cohorts
        keep = stable_mask([assoc_all[n] for n in sel], feats)
        cols = list(np.where(keep)[0])
        Xt, yt = coh[T]
        fit_X, fit_y = training_for_target(d, T)
        reference = cb().fit(fit_X, fit_y) if T == "India/Mumbai" else full
        auc_full = transfer(reference, all_cols, Xt, yt)
        if len(cols) >= 3:
            m = cb().fit(fit_X[:, cols], fit_y)
            auc_stable = transfer(m, cols, Xt, yt)
        else:
            auc_stable = None
        rows.append({"cohort": T, "training_scope": scope(d, T), "n_stable_features": len(cols),
                     "auc_full": auc_full, "auc_stable": auc_stable,
                     "reversed_full": auc_full < 0.5,
                     "reversed_stable": (auc_stable is not None and auc_stable < 0.5)})

    # Test B: mechanism ablation - drop Atopobium (chosen by TRAINING importance only)
    imp = full.get_feature_importance()
    top_train_marker = feats[int(np.argmax(imp))]
    drop = [i for i, f in enumerate(feats) if f == "Atopobium"]
    keep_cols = [i for i in all_cols if i not in drop]
    m_noatop = cb().fit(Xtr[:, keep_cols], ytr)
    Xsa, ysa = coh["South Africa"]
    sa_full = transfer(full, all_cols, Xsa, ysa)
    sa_noatop = transfer(m_noatop, keep_cols, Xsa, ysa)

    out = {
        "params": {"r_vote": R_VOTE, "agree": AGREE, "min_votes": MIN_VOTES,
                   "selection": "leave-one-cohort-out (test cohort excluded from feature selection)"},
        "loco": rows,
        "ablation": {"top_training_marker": top_train_marker,
                     "dropped": "Atopobium",
                     "sa_transfer_full": sa_full,
                     "sa_transfer_no_atopobium": sa_noatop},
        "summary": {
            "mean_transfer_full": round(float(np.mean([r["auc_full"] for r in rows])), 3),
            "mean_transfer_stable": round(float(np.mean([r["auc_stable"] for r in rows if r["auc_stable"] is not None])), 3),
            "n_reversed_full": sum(r["reversed_full"] for r in rows),
            "n_reversed_stable": sum(r["reversed_stable"] for r in rows),
        },
    }
    out["provenance"] = {**d["eligibility"], "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out, indent=2) + "\n")

    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"Test A - LOCO stable-restricted vs full-feature transfer:")
    print(f"  {'cohort':14s} {'#stable':>7s} {'full':>7s} {'stable':>7s}")
    for r in rows:
        flag = ""
        if r["reversed_full"] and not r["reversed_stable"]:
            flag = "  <- de-inverted"
        elif r["reversed_stable"]:
            flag = "  <- still reversed"
        print(f"  {r['cohort']:14s} {r['n_stable_features']:7d} {r['auc_full']:7.3f} "
              f"{str(r['auc_stable']):>7s}{flag}")
    s = out["summary"]
    print(f"  mean transfer: full {s['mean_transfer_full']} | stable {s['mean_transfer_stable']} "
          f"| reversed cohorts: full {s['n_reversed_full']} -> stable {s['n_reversed_stable']}")
    print(f"\nTest B - drop Atopobium (top training marker: {top_train_marker}):")
    print(f"  South Africa transfer: full {sa_full} -> no-Atopobium {sa_noatop}")


if __name__ == "__main__":
    main()
