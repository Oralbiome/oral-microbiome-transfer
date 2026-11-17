#!/usr/bin/env python3
"""NHANES age/sex-only baseline (see PREREGISTRATION_AGE_SEX_BASELINE.md).

Stages: `controls` (C1-C4) then `primary`. Primary refuses to run unless the
controls file exists and every control passed.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed"
SEED = 42
BOOT = 2000
KNOT_PCT = (5, 35, 65, 95)
STRATA = [("<40", -np.inf, 40), ("40-55", 40, 55), ("55-65", 55, 65), ("65+", 65, np.inf)]


# ---- pure helpers (unit-tested) -------------------------------------------
def knots_from(train_age):
    return np.percentile(np.asarray(train_age, float), KNOT_PCT)


def rcs_basis(age, knots):
    """Harrell restricted cubic spline: linear term + (k-2) nonlinear terms."""
    x = np.asarray(age, float)
    k = np.asarray(knots, float)
    p = lambda v: np.maximum(v, 0.0) ** 3
    cols = [x]
    for j in range(len(k) - 2):
        cols.append(p(x - k[j]) - p(x - k[-2]) * (k[-1] - k[j]) / (k[-1] - k[-2])
                    + p(x - k[-1]) * (k[-2] - k[j]) / (k[-1] - k[-2]))
    scale = np.r_[1.0, np.full(len(cols) - 1, (k[-1] - k[0]) ** 2)]
    return np.column_stack(cols) / scale


def design(age, sex, knots, extra=None):
    cols = [rcs_basis(age, knots), np.asarray(sex, float)[:, None]]
    if extra is not None:
        cols.append(np.asarray(extra, float)[:, None])
    Z = np.hstack(cols)
    return Z


def fit_predict_A(age_tr, sex_tr, y_tr, age_te, sex_te, extra_tr=None, extra_te=None):
    """Age spline + sex logistic fit; knots from TRAINING rows only."""
    knots = knots_from(age_tr)
    Ztr, Zte = design(age_tr, sex_tr, knots, extra_tr), design(age_te, sex_te, knots, extra_te)
    mu, sd = Ztr.mean(0), Ztr.std(0) + 1e-12
    clf = LogisticRegression(penalty=None, max_iter=5000).fit((Ztr - mu) / sd, y_tr)
    return clf.predict_proba((Zte - mu) / sd)[:, 1], knots


def paired_bootstrap(y, scores, reps=BOOT, seed=SEED):
    """scores: dict name -> array. Stratified (cases/controls separately), same indices
    for every model. Returns dict name -> AUC draws."""
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    draws = {k: np.empty(reps) for k in scores}
    for r in range(reps):
        s = np.r_[rng.choice(pos, len(pos)), rng.choice(neg, len(neg))]
        for k, v in scores.items():
            draws[k][r] = roc_auc_score(y[s], np.asarray(v)[s])
    return draws


def ci(x):
    return [float(v) for v in np.quantile(x, [.025, .975])]


def decide(lo, hi):
    if lo > 0:
        return "microbiome adds discrimination beyond age+sex in NHANES"
    if hi < 0:
        return "adding microbiome hurts"
    return "no evidence microbiome adds beyond age+sex"


def b_vs_a_reading(point, lo, hi):
    if lo > 0:
        return "microbiome-only discrimination is better than age+sex"
    if point <= 0 or hi <= 0:
        return "microbiome-only discrimination is no better than age+sex"
    return "inconclusive (positive point estimate, CI includes 0)"


def assert_no_leak(folds, n):
    seen = np.zeros(n, int)
    for tr, te in folds:
        if np.intersect1d(tr, te).size:
            raise AssertionError("row in both train and test")
        if len(tr) + len(te) != n:
            raise AssertionError("fold does not partition rows")
        seen[te] += 1
    if not (seen == 1).all():
        raise AssertionError("each row must be tested exactly once")


# ---- data ----------------------------------------------------------------
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git_sha():
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def setup():
    from reconstruct_validation import load, model
    d, X, y, groups = load()
    demo = pd.read_csv(ROOT / "data/processed/nhanes_demographics.csv").set_index("SEQN")
    idx = np.flatnonzero(np.char.lower(groups) == "nhanes")
    seqn = np.asarray(d["study_labels"].index)[idx].astype(float).astype(int)
    if not np.isin(seqn, demo.index).all():
        raise ValueError("NHANES rows lack demographics")
    rows = demo.loc[seqn]
    if rows[["RIDAGEYR", "RIAGENDR"]].isna().any().any():
        raise ValueError("Rows lack age/sex; revise design before reading results")
    age = np.full(len(y), np.nan)
    sex = np.full(len(y), np.nan)
    age[idx] = rows.RIDAGEYR.to_numpy(float)
    sex[idx] = (rows.RIAGENDR.to_numpy(float) == 2).astype(float)  # 1 = female
    folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(X, y))
    assert_no_leak(folds, len(y))
    n, cases = len(idx), int(y[idx].sum())
    if (n, cases) != (9683, 830):
        raise ValueError(f"NHANES population {n}/{cases} != preregistered 9683/830")
    return dict(X=X, y=y, idx=idx, age=age, sex=sex, folds=folds, model=model, n=n, cases=cases)


def oof_A(S, y, extra=None):
    """Logistic age+sex model, NHANES rows only; returns scores aligned to S['idx']."""
    idx, pos = S["idx"], {r: i for i, r in enumerate(S["idx"])}
    p = np.full(len(idx), np.nan)
    for tr, te in S["folds"]:
        tr_n, te_n = np.intersect1d(tr, idx), np.intersect1d(te, idx)
        e_tr = None if extra is None else extra[[pos[r] for r in tr_n]]
        e_te = None if extra is None else extra[[pos[r] for r in te_n]]
        s, _ = fit_predict_A(S["age"][tr_n], S["sex"][tr_n], y[tr_n], S["age"][te_n], S["sex"][te_n], e_tr, e_te)
        p[[pos[r] for r in te_n]] = s
    assert not np.isnan(p).any()
    return p


def oof_cat(S, y, features="micro", pooled=True):
    X = S["X"]
    if features == "micro_agesex":
        X = np.column_stack([X, S["age"], S["sex"]])
    idx = S["idx"]
    pr = np.full(len(y), np.nan)
    for tr, te in S["folds"]:
        if not pooled:
            tr = np.intersect1d(tr, idx)
        te_n = np.intersect1d(te, idx)
        pr[te_n] = S["model"]().fit(X[tr], y[tr]).predict_proba(X[te_n])[:, 1]
    return pr[idx]


def auc(y, s):
    return float(roc_auc_score(y, s))


# ---- stages --------------------------------------------------------------
def controls(S):
    y, idx = S["y"], S["idx"]
    yn = y[idx]
    res = {"n": S["n"], "cases": S["cases"], "git_sha": git_sha(), "seed": SEED, "bootstrap_reps": BOOT}
    pA = oof_A(S, y)
    pB = oof_cat(S, y)
    # C1
    published = json.loads((OUT / "validation_subgroups.json").read_text())["overall"]["auc"]
    aB = auc(yn, pB)
    res["C1"] = {"published_auc": published, "reproduced_auc_B": aB, "abs_diff": abs(aB - published),
                 "tolerance": 0.005, "pass": bool(abs(aB - 0.698) <= 0.005)}
    print("C1", res["C1"], flush=True)
    # C2
    rng = np.random.default_rng(SEED)
    permA, permC = [], []
    for i in range(20):
        yp = rng.permutation(y)
        permA.append(auc(yp[idx], oof_A(S, yp)))
    for i in range(5):
        yp = rng.permutation(y)
        permC.append(auc(yp[idx], oof_cat(S, yp, "micro_agesex")))
        print("perm C", i, permC[-1], flush=True)
    res["C2"] = {"A_perm_aucs": permA, "C_perm_aucs": permC, "A_mean": float(np.mean(permA)),
                 "C_mean": float(np.mean(permC)), "range": [0.47, 0.53],
                 "pass": bool(0.47 <= np.mean(permA) <= 0.53 and 0.47 <= np.mean(permC) <= 0.53)}
    print("C2", res["C2"]["A_mean"], res["C2"]["C_mean"], flush=True)
    # C3
    d = np.sqrt(2) * norm.ppf(0.75)
    z = d * yn + np.random.default_rng(SEED + 1).normal(size=len(yn))
    pS = oof_A(S, y, extra=z)
    dr = paired_bootstrap(yn, {"A": pA, "S": pS})
    diff = dr["S"] - dr["A"]
    res["C3"] = {"synthetic_marginal_auc": auc(yn, z), "auc_A": auc(yn, pA), "auc_A_plus_synthetic": auc(yn, pS),
                 "delta_ci95": ci(diff), "pass": bool(ci(diff)[0] > 0 and auc(yn, pS) >= 0.70)}
    print("C3", res["C3"], flush=True)
    # C4
    assert_no_leak(S["folds"], len(y))
    chk = []
    for tr, te in S["folds"]:
        tr_n, te_n = np.intersect1d(tr, idx), np.intersect1d(te, idx)
        k = knots_from(S["age"][tr_n])
        chk.append(bool(np.allclose(k, np.percentile(S["age"][tr_n], KNOT_PCT)) and not np.intersect1d(tr_n, te_n).size))
    res["C4"] = {"folds_disjoint_partition": True, "knots_from_train_only": chk, "pass": bool(all(chk))}
    res["all_pass"] = bool(all(res[c]["pass"] for c in ("C1", "C2", "C3", "C4")))
    res["input_sha256"] = {n: sha(ROOT / n) for n in ("data/models/processed_data_vsearch.pkl", "data/processed/nhanes_demographics.csv")}
    (OUT / "baseline_age_sex_controls_v1.json").write_text(json.dumps(res, indent=2) + "\n")
    print("controls all_pass:", res["all_pass"])
    return res["all_pass"]


def primary(S):
    c = json.loads((OUT / "baseline_age_sex_controls_v1.json").read_text())
    if not c.get("all_pass"):
        raise SystemExit("Controls did not all pass; primaries must not run")
    y, idx = S["y"], S["idx"]
    yn = y[idx]
    P = {"A": oof_A(S, y), "B": oof_cat(S, y), "C": oof_cat(S, y, "micro_agesex"),
         "B_nh": oof_cat(S, y, "micro", pooled=False), "C_nh": oof_cat(S, y, "micro_agesex", pooled=False)}
    dr = paired_bootstrap(yn, P)
    res = {"n": S["n"], "cases": S["cases"], "git_sha": git_sha(), "fold_seed": SEED, "bootstrap_seed": SEED,
           "bootstrap_reps": BOOT, "weights": "unweighted",
           "preregistration": "PREREGISTRATION_AGE_SEX_BASELINE.md",
           "controls_file": "data/processed/baseline_age_sex_controls_v1.json",
           "input_sha256": c["input_sha256"], "auc": {}, "delta": {}}
    for k, v in P.items():
        res["auc"][k] = {"auc": auc(yn, v), "ci95": ci(dr[k])}
    for name, a, b in [("C_minus_A", "C", "A"), ("B_minus_A", "B", "A"), ("C_minus_B", "C", "B"),
                       ("C_nh_minus_A", "C_nh", "A"), ("B_nh_minus_A", "B_nh", "A")]:
        diff = dr[a] - dr[b]
        res["delta"][name] = {"delta": res["auc"][a]["auc"] - res["auc"][b]["auc"], "ci95": ci(diff)}
    d = res["delta"]["C_minus_A"]
    res["decision_C_minus_A"] = decide(*d["ci95"])
    b = res["delta"]["B_minus_A"]
    res["reading_B_vs_A"] = b_vs_a_reading(b["delta"], *b["ci95"])
    age = S["age"][idx]
    sexv = S["sex"][idx]
    res["strata"] = {}
    groups = [(f"age {n}", (age >= lo) & (age < hi)) for n, lo, hi in STRATA] + \
             [("sex male", sexv == 0), ("sex female", sexv == 1)]
    for name, m in groups:
        row = {"n": int(m.sum()), "cases": int(yn[m].sum())}
        for k in ("A", "B", "C"):
            row[k] = auc(yn[m], P[k][m]) if 0 < yn[m].sum() < m.sum() else None
        res["strata"][name] = row
    (OUT / "baseline_age_sex_v1.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: res[k] for k in ("auc", "delta", "decision_C_minus_A", "reading_B_vs_A")}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["controls", "primary"])
    a = ap.parse_args()
    S = setup()
    if a.stage == "controls":
        sys.exit(0 if controls(S) else 1)
    primary(S)
