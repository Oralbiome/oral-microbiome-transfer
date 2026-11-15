"""Oral-only eligibility contract; never silently overwrite the historical matrix.

PRJNA910326 contains both oral (DT/HT) and fecal (DF) samples. The
historical sample_type column labels them all tongue_coating and cannot be used
for eligibility. The deposited aliases, corroborated by the original paper,
identify the 129 fecal rows to exclude. Retain the historical 139-column rank
space as a retrospective, fixed vocabulary, not a newly validated assay.
"""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/models/processed_data_vsearch.pkl"
META = ROOT / "data/processed/china_shanghai_t2dm_metadata.csv"
INPUTS = ["data/processed/unified_genus_counts.csv",
          "data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv",
          "data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv",
          "data/interim/sa_genus_counts.csv", "data/raw/south_africa/labels.tsv",
          "data/processed/nhanes_demographics.csv", "data/processed/nhanes_demographics.provenance.json"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance():
    return {"input_sha256": sha(DATA), "eligibility_metadata_sha256": sha(META),
            "auxiliary_input_sha256": {name: sha(ROOT / name) for name in INPUTS},
            "transfer_contract_sha256": sha(ROOT / 'scripts/transfer_contract.py'),
            "eligibility_code_sha256": sha(Path(__file__)),
            "eligibility_rule": "Shanghai DT/HT oral aliases retained; DF fecal aliases excluded",
            "excluded_fecal_rows": 129, "source_n": 10228, "source_cases": 1251,
            "feature_scope": "fixed historical 139-genus rank vocabulary; retrospective"}


def load_data():
    data = pd.read_pickle(DATA)
    ids = data["study_labels"].index
    if not ids.is_unique or not ids.equals(data["X_train_df"].index):
        raise ValueError("Source sample identity is duplicate or misaligned")
    metadata = pd.read_csv(META, index_col="sample_id")
    if not metadata.index.is_unique or not metadata["sample_alias"].is_unique:
        raise ValueError("Shanghai deposited sample identities must be unique")
    shanghai = np.asarray(data["study_labels"]) == "china_shanghai_t2dm"
    aliases = metadata.loc[ids[shanghai], "sample_alias"].astype(str)
    prefix = aliases.str[:2]
    if not prefix.isin(["DT", "HT", "DF"]).all():
        raise ValueError("Unresolved Shanghai specimen alias; do not guess eligibility")
    keep = np.ones(len(ids), dtype=bool)
    keep[np.flatnonzero(shanghai)] = prefix.isin(["DT", "HT"])
    if (~keep).sum() != 129:
        raise ValueError("Eligibility inputs changed; re-audit before regenerating claims")
    for key in ("X_train", "y_train"):
        data[key] = np.asarray(data[key])[keep]
    for key in ("study_labels", "X_train_df"):
        data[key] = data[key].iloc[np.flatnonzero(keep)]
    if len(data["y_train"]) != 10228 or data["y_train"].sum() != 1251:
        raise ValueError("Audited source composition changed")
    data["eligibility"] = provenance()
    return data
