#!/usr/bin/env python
"""Research adaptation reference; not clinical calibration or a deployable assay.

The exported logistic uses 10,228 oral-only source rows (US, China, India).
Local adaptation needs labeled samples disjoint from the global source and
independent evaluation. Output scores are not validated disease probabilities.
The prospective protocol, thresholds, consent, and clinical utility are unproven.
See docs/Calibration_Model_Card.md and the corrected preprint.

Usage: python scripts/calibrate.py export|demo|calibrate|predict|curve
"""
import argparse, json, sys
from pathlib import Path
from audited_data import load_data
import numpy as np
from scipy.stats import rankdata
from scipy.optimize import minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_PATH = ROOT / "data" / "models" / "global_logistic.json"
LAM = 2.0  # prior strength: shrink calibrated coefficients toward the global directions


# ------------------------------------------------------------------ core model
def _fit_prior_logistic(X, y, beta0, b0, lam):
    """Logistic regression shrunk toward a prior coefficient vector beta0 (L-BFGS)."""
    X = np.asarray(X, float); y = np.asarray(y, float); n, d = X.shape

    def obj(w):
        beta, b = w[:d], w[d]
        p = expit(X @ beta + b)
        eps = 1e-9
        ll = -np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
        reg = 0.5 * lam * np.sum((beta - beta0) ** 2)
        g = np.concatenate([X.T @ (p - y) + lam * (beta - beta0), [np.sum(p - y)]])
        return ll + reg, g

    res = minimize(obj, np.concatenate([beta0, [b0]]), jac=True, method="L-BFGS-B",
                   options={"maxiter": 200})
    return res.x[:d], float(res.x[d])


def rank_transform(counts, feature_names):
    """Genus-count DataFrame (rows = samples, cols = genera) -> per-sample rank matrix
    in the model's feature order. Missing genera are filled with zero, exactly as at
    training time; the rank transform is per-sample and so leakage-free."""
    import pandas as pd
    X = counts.reindex(columns=feature_names, fill_value=0).astype(float)
    if not len(X) or not np.isfinite(X.values).all() or (X.values < 0).any():
        raise ValueError('Counts must have nonempty rows and finite, nonnegative values')
    return np.vstack([rankdata(row, method="average") / len(row) for row in X.values])


def load_global(path=GLOBAL_PATH):
    if not Path(path).exists():
        sys.exit(f"No global model at {path}. Run: python calibrate.py export")
    g = json.loads(Path(path).read_text())
    g["coef"] = np.asarray(g["coef"], float)
    return g


def calibrate(counts_local, y_local, g, lam=LAM):
    """Fit a population-calibrated model from k labeled local samples."""
    reject_source_overlap(counts_local)
    X = rank_transform(counts_local, g["feature_names"])
    y = np.asarray(y_local, int)
    beta, b = _fit_prior_logistic(X, y, g["coef"], g["intercept"], lam)
    n_flips = int(np.sum(np.sign(beta) != np.sign(g["coef"])))
    return {"feature_names": g["feature_names"], "coef": beta.tolist(), "intercept": b,
            "lambda": lam, "n_calibration": int(len(y)), "n_sign_flips_vs_global": n_flips,
            "base": "global_logistic"}


def predict_proba(model, counts):
    coef = np.asarray(model["coef"], float)
    X = rank_transform(counts, model["feature_names"])
    return expit(X @ coef + model["intercept"])


# ------------------------------------------------------------------ evaluation
def reject_source_overlap(counts):
    source = set(map(str, load_data()['study_labels'].index))
    overlap = source & set(map(str, counts.index))
    if overlap:
        raise ValueError(f'{len(overlap)} local rows overlap the global source; export a source-study-excluded model before independent local evaluation')


def calibration_curve(counts, y, g, ks=(0, 5, 10, 20, 40), seeds=12, lam=LAM):
    """AUC vs number of local labels for a cohort (leakage-free repeated 5-fold).
    Tells a deploying lab roughly how many labels it needs."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    reject_source_overlap(counts)
    X = rank_transform(counts, g["feature_names"]); y = np.asarray(y, int)
    out = []
    for k in ks:
        aucs = []
        for seed in range(seeds):
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            pr, yy = [], []
            for tr, te in skf.split(X, y):
                if k == 0:
                    p = expit(X[te] @ g["coef"] + g["intercept"])
                else:
                    rng = np.random.RandomState(seed * 100 + len(te))
                    cal = tr[_stratified_take(y[tr], k, rng)]
                    if y[cal].sum() < 1 or (y[cal] == 0).sum() < 1:
                        p = expit(X[te] @ g["coef"] + g["intercept"])
                    else:
                        beta, b = _fit_prior_logistic(X[cal], y[cal], g["coef"], g["intercept"], lam)
                        p = expit(X[te] @ beta + b)
                pr.extend(p); yy.extend(y[te])
            if len(set(yy)) == 2:
                aucs.append(roc_auc_score(yy, pr))
        out.append({"k": k, "auc": round(float(np.mean(aucs)), 3)})
    return out


def _stratified_take(y, k, rng):
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    kp = min(max(1, round(k * len(pos) / len(y))), len(pos))
    kn = min(max(1, k - kp), len(neg))
    return np.concatenate([rng.choice(pos, kp, False), rng.choice(neg, kn, False)])


# ------------------------------------------------------------------ CLI
def _read_counts(path):
    import pandas as pd
    return pd.read_csv(path, index_col=0)


def _read_labels(path, index):
    import pandas as pd
    lab = pd.read_csv(path, sep="\t", header=None)
    lab = lab.set_index(lab.columns[0])[lab.columns[-1]]
    common = [s for s in index if s in lab.index and lab.loc[s] in (0, 1)]
    return common, lab.loc[common].astype(int).values


def cmd_export(_):
    """Fit the frozen global logistic on the pooled training data and export it."""
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    d = load_data()
    feats = list(d["feature_names"])
    Xtr, ytr = np.asarray(d["X_train"], float), np.asarray(d["y_train"], int)
    m = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000).fit(Xtr, ytr)
    sl = np.asarray(d["study_labels"])
    GLOBAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_PATH.write_text(json.dumps({
        "model": "logistic regression, 139-genus per-sample rank space",
        "feature_names": feats,
        "coef": m.coef_.ravel().tolist(),
        "intercept": float(m.intercept_[0]),
        "provenance": {"training_pool": "Oral-only NHANES (US), China, and India", "eligibility": d["eligibility"], "n": int(len(ytr)),
                       "cases": int(ytr.sum()), "controls": int((ytr == 0).sum()),
                       "studies": sorted(set(sl.tolist()))},
        "pipeline": "VSEARCH closed-ref HOMD v16.03 -> genus counts -> reindex 139 feats -> per-sample rank",
    }, indent=2) + "\n")
    print(f"WROTE {GLOBAL_PATH.relative_to(ROOT)}  ({len(feats)} features, n={len(ytr)})")


def cmd_demo(_):
    """Worked example: treat South Africa (checked-in) as a new population and show
    that a few local labels de-invert the reversed global model."""
    from sklearn.metrics import roc_auc_score
    g = load_global()
    counts = _read_counts(ROOT / "data/interim/sa_genus_counts.csv")
    common, y = _read_labels(ROOT / "data/raw/south_africa/labels.tsv", counts.index)
    counts = counts.loc[common]
    transfer = roc_auc_score(y, predict_proba(g, counts))
    print(f"Demo: South Africa as a new population (n={len(y)}, {int(y.sum())} T2D / {int((y==0).sum())} control)")
    print(f"  global model, no calibration:  AUC {transfer:.3f}"
          + ("  (reversed, read backwards)" if transfer < 0.5 else ""))
    print("  calibration curve (labels -> AUC):")
    for pt in calibration_curve(counts, y, g):
        tag = "  <- crosses chance" if pt["auc"] >= 0.5 and pt["k"] > 0 else ""
        print(f"    {pt['k']:3d} labels : {pt['auc']:.3f}{tag}")
    model = calibrate(counts, y, g)   # calibrate on the whole cohort to show sign flips
    print(f"  calibrated on {model['n_calibration']} labels: {model['n_sign_flips_vs_global']} "
          f"marker directions flipped vs the global model")
    print("  (this is a reference demo; deploy with disjoint calibration and evaluation sets)")


def cmd_calibrate(a):
    g = load_global()
    counts = _read_counts(a.counts)
    common, y = _read_labels(a.labels, counts.index)
    model = calibrate(counts.loc[common], y, g, lam=a.lam)
    Path(a.out).write_text(json.dumps(model, indent=2) + "\n")
    print(f"WROTE {a.out}  (calibrated on {model['n_calibration']} labels, "
          f"{model['n_sign_flips_vs_global']} sign flips vs global)")


def cmd_predict(a):
    model = json.loads(Path(a.model).read_text())
    counts = _read_counts(a.counts)
    p = predict_proba(model, counts)
    lines = ["sample,p_t2d"] + [f"{s},{prob:.4f}" for s, prob in zip(counts.index, p)]
    if a.out:
        Path(a.out).write_text("\n".join(lines) + "\n"); print(f"WROTE {a.out} ({len(p)} samples)")
    else:
        print("\n".join(lines))


def cmd_curve(a):
    g = load_global()
    counts = _read_counts(a.counts)
    common, y = _read_labels(a.labels, counts.index)
    for pt in calibration_curve(counts.loc[common], y, g):
        print(f"  {pt['k']:3d} labels : AUC {pt['auc']:.3f}")


def main():
    p = argparse.ArgumentParser(description="Global-model + per-population calibration (experiment #4 artifact).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export").set_defaults(fn=cmd_export)
    sub.add_parser("demo").set_defaults(fn=cmd_demo)
    c = sub.add_parser("calibrate"); c.add_argument("--counts", required=True); c.add_argument("--labels", required=True)
    c.add_argument("--out", required=True); c.add_argument("--lam", type=float, default=LAM); c.set_defaults(fn=cmd_calibrate)
    pr = sub.add_parser("predict"); pr.add_argument("--model", required=True); pr.add_argument("--counts", required=True)
    pr.add_argument("--out"); pr.set_defaults(fn=cmd_predict)
    cv = sub.add_parser("curve"); cv.add_argument("--counts", required=True); cv.add_argument("--labels", required=True)
    cv.set_defaults(fn=cmd_curve)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
