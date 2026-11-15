#!/usr/bin/env python3
"""Reconstruct disputed analyses on the tracked VSEARCH matrix.

Source studies alone select the panel and fit calibrators. Already-inspected
external cohorts remain exploratory benchmarks, never an untouched test set.
Run --section panel, calibration, permutation, or all; outputs are versioned JSON.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import catboost
from catboost import CatBoostClassifier, Pool
import numpy as np
import pandas as pd
import sklearn
from audited_data import load_data, provenance as eligibility_provenance
from transfer_contract import BENCHMARKS, training_mask, scope
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/models/processed_data_vsearch.pkl"
OUT = ROOT / "data/processed"
SEED = 42
PARAMS = dict(iterations=200, depth=4, learning_rate=0.1,
              auto_class_weights="Balanced", verbose=False,
              allow_writing_files=False, thread_count=4)


def model(seed=SEED):
    return CatBoostClassifier(**PARAMS, random_seed=seed)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance():
    return {
        "schema_version": 1, "input": str(DATA.relative_to(ROOT)),
        "eligibility": eligibility_provenance(),
        "input_sha256": sha(DATA), "script_sha256": sha(Path(__file__)),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "catboost": catboost.__version__,
                     "sklearn": sklearn.__version__},
        "parameters": PARAMS, "seed": SEED,
        "external_status": "exploratory: previously inspected during development",
    }


def save(name, result):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"validation_{name}.json"
    path.write_text(json.dumps({**provenance(), **result}, indent=2) + "\n")
    print(f"Wrote {path.relative_to(ROOT)}", flush=True)


def load():
    d = load_data()
    return d, np.asarray(d["X_train"]), np.asarray(d["y_train"], dtype=int), np.asarray(d["study_labels"]).astype(str)


def shap_order(fitted, X, y, seed=SEED):
    """Rank ALL columns using SHAP on training rows only (sample <=1,024)."""
    idx = np.random.default_rng(seed).choice(len(y), min(1024, len(y)), replace=False)
    values = fitted.get_feature_importance(Pool(X[idx], y[idx]), type="ShapValues")[:, :-1]
    importance = np.mean(np.abs(values), axis=0)
    return np.argsort(-importance, kind="stable"), importance


def auc(y, scores):
    return float(roc_auc_score(y, scores))


def summarize(values):
    values = np.asarray(values)
    return {"mean": float(values.mean()), "sd": float(values.std(ddof=1)),
            "seed_percentiles_2_5_97_5": np.quantile(values, [.025, .975]).tolist()}


def study_select(X, y, groups):
    """Choose K from source studies by macro mean leave-one-study-out AUC."""
    scores = {30: [], X.shape[1]: []}
    for group in np.unique(groups):
        train, valid = groups != group, groups == group
        base = model().fit(X[train], y[train])
        order, _ = shap_order(base, X[train], y[train])
        panel = model().fit(X[train][:, order[:30]], y[train])
        scores[X.shape[1]].append(auc(y[valid], base.predict_proba(X[valid])[:, 1]))
        scores[30].append(auc(y[valid], panel.predict_proba(X[valid][:, order[:30]])[:, 1]))
    means = {k: float(np.mean(v)) for k, v in scores.items()}
    # On an exact tie retain all features, avoiding an unsupported panel reduction.
    choice = max(means, key=lambda k: (means[k], k))
    return choice, {str(k): {"study_aucs": v, "macro_auc": means[k]} for k, v in scores.items()}


def panel_analysis(n_seeds):
    d, X, y, groups = load()
    folds = []
    for group in np.unique(groups):
        train, valid = groups != group, groups == group
        selected, inner = study_select(X[train], y[train], groups[train])
        base = model().fit(X[train], y[train])
        order, _ = shap_order(base, X[train], y[train])
        panel = model().fit(X[train][:, order[:30]], y[train])
        fixed = {"139": auc(y[valid], base.predict_proba(X[valid])[:, 1]),
                 "30": auc(y[valid], panel.predict_proba(X[valid][:, order[:30]])[:, 1])}
        folds.append({"held_study": group, "n": int(valid.sum()), "selected_k": selected,
                      "inner": inner, "fixed_k_auc": fixed, "selected_auc": fixed[str(selected)],
                      "features_30": [d["feature_names"][i] for i in order[:30]]})
        print(f"Nested LOSO {group}: K={selected}, AUC={fixed[str(selected)]:.3f}", flush=True)
    selected, selection = study_select(X, y, groups)
    base = model().fit(X, y)
    order, importance = shap_order(base, X, y)
    panel = model().fit(X[:, order[:30]], y)
    external = {}
    predictions = [[], [], []]
    for name, suffix in BENCHMARKS:
        txbase, txpanel, txorder = base, panel, order
        if name == "Shanghai/related":
            mask = training_mask(d, name)
            txbase = model().fit(X[mask], y[mask])
            txorder, _ = shap_order(txbase, X[mask], y[mask])
            txpanel = model().fit(X[mask][:, txorder[:30]], y[mask])
        tx, ty = np.asarray(d[f"X_{suffix}"]), np.asarray(d[f"y_{suffix}"])
        fullp, panelp = txbase.predict_proba(tx)[:, 1], txpanel.predict_proba(tx[:, txorder[:30]])[:, 1]
        external[name] = {"n": len(ty), "full_auc": auc(ty, fullp),
                          "panel30_auc": auc(ty, panelp), "training_scope": scope(d, name)}
        for dest, value in zip(predictions, (ty, fullp, panelp)):
            dest.append(value)
    ty, fullp, panelp = map(np.concatenate, predictions)
    external["three_cohort_pooled"] = {"n": len(ty), "full_auc": auc(ty, fullp),
        "panel30_auc": auc(ty, panelp), "note": "Descriptive pooled benchmark with different source fits; Shanghai source study excluded for related benchmark."}
    nhanes = np.flatnonzero(np.char.lower(groups) == "nhanes")
    other = np.flatnonzero(np.char.lower(groups) != "nhanes")
    if len(nhanes) < 500:
        raise ValueError("Expected >=500 NHANES rows; source-study labels do not match")
    runs = []
    for seed in range(n_seeds):
        idx = np.r_[np.random.default_rng(seed).choice(nhanes, 500, replace=False), other]
        full = model(seed).fit(X[idx], y[idx])
        rank, _ = shap_order(full, X[idx], y[idx], seed)
        small = model(seed).fit(X[idx][:, rank[:30]], y[idx])
        tx, ty = np.asarray(d["X_holdout"]), np.asarray(d["y_holdout"])
        runs.append({"seed": seed, "n_source": len(idx),
                     "full_auc": auc(ty, full.predict_proba(tx)[:, 1]),
                     "panel30_auc": auc(ty, small.predict_proba(tx[:, rank[:30]])[:, 1]),
                     "features_30": [d["feature_names"][i] for i in rank[:30]]})
        if (seed + 1) % 10 == 0:
            print(f"Paired NHANES=500 reconstruction: {seed + 1}/{n_seeds}", flush=True)
    save("panel", {
        "protocol": "nested leave-one-source-study-out; inner macro-study AUC selects K=30 or 139; SHAP ranking refit on training rows only",
        "nested_loso": {"folds": folds, "macro_auc": float(np.mean([f["selected_auc"] for f in folds]))},
        "source_selection": {"selected_k": selected, "candidates": selection},
        "shap_ranking": [{"feature": d["feature_names"][i], "mean_abs_shap": float(importance[i])} for i in order],
        "external_benchmarks": external,
        "downsample_reconstruction": {
            "n_seeds": n_seeds, "nhanes_n": 500, "runs": runs,
            "full": summarize([r["full_auc"] for r in runs]),
            "panel30": summarize([r["panel30_auc"] for r in runs]),
            "panel_wins": sum(r["panel30_auc"] > r["full_auc"] for r in runs),
            "uncertainty_note": "Seed percentiles describe algorithm/subsample variability on the same 50-person benchmark, not a patient confidence interval or independent replications.",
        },
        "limitations": "Source-only nesting prevents row leakage but cannot undo prior choice of CatBoost/parameters. Six studies give high-variance macro AUC; this reconstruction is retrospective. A new untouched cohort is required for confirmatory transfer evaluation.",
    })


def ece(y, p, n_bins=10):
    bins = np.minimum((np.asarray(p) * n_bins).astype(int), n_bins - 1)
    return float(sum(np.mean(bins == b) * abs(np.mean(y[bins == b]) - np.mean(p[bins == b]))
                     for b in range(n_bins) if np.any(bins == b)))


def metrics(y, p):
    return {"auc": auc(y, p), "brier": float(brier_score_loss(y, p)), "ece10": ece(y, p),
            "n": len(y), "prevalence": float(np.mean(y))}


def calibration_analysis():
    d, X, y, _ = load()
    raw, calibrated = np.zeros(len(y)), np.zeros(len(y))
    ext = {suffix: [[], []] for _, suffix in BENCHMARKS}
    folds = []
    for fold, (development, test) in enumerate(StratifiedKFold(5, shuffle=True, random_state=SEED).split(X, y)):
        fit, cal = train_test_split(development, test_size=.25, stratify=y[development], random_state=SEED + fold)
        # All three row sets must be disjoint. Never fit on evaluation labels.
        assert not (set(fit) & set(cal) or set(fit) & set(test) or set(cal) & set(test))
        fitted = model().fit(X[fit], y[fit])
        iso = IsotonicRegression(out_of_bounds="clip").fit(fitted.predict_proba(X[cal])[:, 1], y[cal])
        raw[test] = fitted.predict_proba(X[test])[:, 1]
        calibrated[test] = iso.predict(raw[test])
        folds.append({"fold": fold, "fit_n": len(fit), "calibration_n": len(cal), "test_n": len(test),
                      "raw": metrics(y[test], raw[test]), "calibrated": metrics(y[test], calibrated[test])})
        for suffix in ext:
            current_model, current_iso = fitted, iso
            if suffix == "holdout_782768":
                mask = training_mask(d, "Shanghai/related")
                related_fit, related_cal = fit[mask[fit]], cal[mask[cal]]
                current_model = model().fit(X[related_fit], y[related_fit])
                current_iso = IsotonicRegression(out_of_bounds="clip").fit(current_model.predict_proba(X[related_cal])[:, 1], y[related_cal])
            p = current_model.predict_proba(np.asarray(d[f"X_{suffix}"]))[:, 1]
            ext[suffix][0].append(p)
            ext[suffix][1].append(current_iso.predict(p))
    combined = {suffix: [np.mean(v, axis=0) for v in preds] for suffix, preds in ext.items()}
    combined["holdout_all"] = [np.concatenate([combined[suffix][i] for _, suffix in BENCHMARKS]) for i in (0, 1)]
    save("calibration", {
        "protocol": "5 outer stratified folds; each development fold splits 75% model fit / 25% calibration; evaluation labels never fit model or isotonic mapping",
        "source_oof": {"raw": metrics(y, raw), "calibrated": metrics(y, calibrated), "folds": folds},
        "external_benchmarks": {suffix: {
            "raw": metrics(np.asarray(d[f"y_{suffix}"]), preds[0]),
            "calibrated": metrics(np.asarray(d[f"y_{suffix}"]), preds[1]),
            "scope": "Shanghai source rows excluded from fitting and calibration for PRJNA782768; pooled scores combine different source fits." if suffix in ("holdout_782768", "holdout_all") else "Oral-only source ensemble; exploratory.",
        } for suffix, preds in combined.items()},
        "limitations": "Calibration targets the source mixture's prevalence. It does not guarantee calibration under study/prevalence shift; external scores are exploratory and ECE is bin-dependent.",
    })


def cv_statistic(X, y):
    """Identical 5-fold mean-AUC procedure for observed and every permutation."""
    scores = []
    for train, test in StratifiedKFold(5, shuffle=True, random_state=SEED).split(X, y):
        fitted = model().fit(X[train], y[train])
        scores.append(auc(y[test], fitted.predict_proba(X[test])[:, 1]))
    return float(np.mean(scores))


def permute_within_studies(y, groups, rng):
    shuffled = y.copy()
    for group in np.unique(groups):
        idx = np.flatnonzero(groups == group)
        shuffled[idx] = rng.permutation(y[idx])
    return shuffled


def permutation_analysis(n_permutations):
    _, X, y, groups = load()
    observed = cv_statistic(X, y)
    rng = np.random.default_rng(SEED)
    null = []
    for i in range(n_permutations):
        null.append(cv_statistic(X, permute_within_studies(y, groups, rng)))
        if (i + 1) % 10 == 0:
            print(f"5-fold within-study permutation: {i + 1}/{n_permutations}; observed={observed:.3f}; null mean={np.mean(null):.3f}", flush=True)
    save("permutation", {
        "protocol": "within-source-study label shuffle preserves case counts and study composition; identical 5-fold mean AUC, splits algorithm, and estimator for observed and all permutations",
        "null_hypothesis": "No within-study feature-label association, conditional on study and study case counts, under within-study exchangeability.",
        "observed_auc": observed, "null_aucs": null, "n_permutations": n_permutations,
        "null_mean": float(np.mean(null)), "null_sd": float(np.std(null, ddof=1)),
        "p_value": float((1 + np.sum(np.asarray(null) >= observed)) / (1 + n_permutations)),
        "limitations": "Conditional association test only. Other within-study confounding remains; this is neither a causal disease test nor a transfer test. Study composition can make null AUC substantially exceed 0.5.",
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=["panel", "calibration", "permutation", "all"], default="all")
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--permutations", type=int, default=100)
    args = parser.parse_args()
    if args.seeds < 2 or args.permutations < 2:
        parser.error("At least two seeds and permutations are required")
    if args.section in ("panel", "all"):
        panel_analysis(args.seeds)
    if args.section in ("calibration", "all"):
        calibration_analysis()
    if args.section in ("permutation", "all"):
        permutation_analysis(args.permutations)


if __name__ == "__main__":
    main()
