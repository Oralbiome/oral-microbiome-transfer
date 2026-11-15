#!/usr/bin/env python3
"""Replace training-resubstitution subgroup scores with source OOF estimates.

Downloads CDC public-use DEMO_F/G if absent; only the public SEQN and demographic
fields used here are retained in a small derived table for offline reproduction.
"""
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from reconstruct_validation import ROOT, DATA, load, metrics, model, provenance, auc

META = ROOT / "data/processed/nhanes_demographics.csv"
SOURCES = [f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/DEMO_{cycle}.xpt"
           for year, cycle in [(2009, "F"), (2011, "G")]]


def metadata():
    if META.exists() and META.with_suffix(".provenance.json").exists():
        return pd.read_csv(META)
    parts, hashes = [], {}
    for url in SOURCES:
        with urlopen(url, timeout=60) as response:
            raw = response.read()
        hashes[url] = hashlib.sha256(raw).hexdigest()
        parts.append(pd.read_sas(io.BytesIO(raw), format="xport")[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDRETH1"]])
    table = pd.concat(parts, ignore_index=True)
    table["SEQN"] = table.SEQN.astype(int)
    table.to_csv(META, index=False)
    META.with_suffix(".provenance.json").write_text(json.dumps({"source_sha256": hashes, "columns": list(table.columns)}, indent=2) + "\n")
    return table


def subgroup(y, p):
    result = metrics(y, p)
    result["cases"] = int(y.sum())
    result["controls"] = int((y == 0).sum())
    result["sensitivity_at_0_5"] = float(np.mean(p[y == 1] >= .5))
    result["specificity_at_0_5"] = float(np.mean(p[y == 0] < .5))
    rng = np.random.default_rng(42)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    scores = []
    for _ in range(2000):
        sample = np.r_[rng.choice(pos, len(pos)), rng.choice(neg, len(neg))]
        scores.append(auc(y[sample], p[sample]))
    result["auc_ci95"] = np.quantile(scores, [.025, .975]).tolist()
    return result


def main():
    d, X, y, groups = load()
    demo = metadata().set_index("SEQN")
    p = np.zeros(len(y))
    for train, test in StratifiedKFold(5, shuffle=True, random_state=42).split(X, y):
        p[test] = model().fit(X[train], y[train]).predict_proba(X[test])[:, 1]
    idx = np.flatnonzero(np.char.lower(groups) == "nhanes")
    seqn = np.asarray(d["study_labels"].index)[idx].astype(float).astype(int)
    if not np.isin(seqn, demo.index).all():
        raise ValueError("Some NHANES matrix rows lack public demographic metadata")
    rows = demo.loc[seqn].reset_index()
    rows["sex"] = rows.RIAGENDR.map({1: "Male", 2: "Female"})
    rows["age"] = pd.cut(rows.RIDAGEYR, [-np.inf, 40, 55, 65, np.inf], right=False, labels=["<40", "40-55", "55-65", "65+"])
    rows["race_ethnicity"] = rows.RIDRETH1.map({1: "Mexican-American", 2: "Other Hispanic", 3: "White", 4: "Black", 5: "Other/Multi"})
    results = {}
    for category in ("sex", "age", "race_ethnicity"):
        results[category] = {}
        for label in rows[category].dropna().unique():
            mask = np.asarray(rows[category] == label)
            results[category][str(label)] = subgroup(y[idx][mask], p[idx][mask])
    result = {**provenance(), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "estimator_script_sha256": hashlib.sha256((ROOT / "scripts/reconstruct_validation.py").read_bytes()).hexdigest(),
              "metadata_sha256": hashlib.sha256(META.read_bytes()).hexdigest(), "metadata_sources": SOURCES,
              "protocol": "Pooled-source 5-fold stratified OOF CatBoost predictions; each NHANES row is scored by a model that did not fit its label. Fixed raw-probability threshold 0.5, not optimized by subgroup.",
              "subgroups": results, "overall": subgroup(y[idx], p[idx]),
              "limitations": "Descriptive discrimination and fixed-threshold error rates, not a fairness certification. Conditional stratified bootstrap intervals omit fold/model/study-selection uncertainty; no survey weights, population calibration, intersectional or prospective evaluation. Raw balanced-class probabilities are not calibrated disease risks."}
    path = ROOT / "data/processed/validation_subgroups.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print("Wrote out-of-fold subgroup estimates with conditional AUC intervals and error rates.")


if __name__ == "__main__":
    main()
