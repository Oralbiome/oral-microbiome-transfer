"""Source/evaluation identity guard for the retrospective transfer benchmarks."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]


def training_mask(data, target):
    groups = np.asarray(data["study_labels"]).astype(str)
    # India/Mumbai is an expanded re-evaluation of the same accession that
    # contributed 50 source rows. Exclude the entire study, not just overlaps.
    if target == "India/Mumbai":
        return np.array([not s.lower().startswith("india") for s in groups])
    if target == "Shanghai/related":
        return groups != "china_shanghai_t2dm"
    return np.ones(len(groups), dtype=bool)


def training_for_target(data, target):
    mask = training_mask(data, target)
    return np.asarray(data["X_train"])[mask], np.asarray(data["y_train"])[mask]


def external_rows(data, target, counts_path, labels_path):
    counts = pd.read_csv(ROOT / counts_path, index_col=0)
    labels = pd.read_csv(ROOT / labels_path, sep="\t", header=None)
    labels = labels.set_index(labels.columns[0])[labels.columns[-1]]
    if not counts.index.is_unique or not labels.index.is_unique:
        raise ValueError(f"Duplicate sample identity in {target} inputs")
    ids = [s for s in counts.index if s in labels.index and labels.loc[s] in (0, 1)]
    mask = training_mask(data, target)
    source_ids = set(map(str, np.asarray(data["study_labels"].index)[mask]))
    overlap = source_ids & set(map(str, ids))
    if overlap:
        raise ValueError(f"{target}: {len(overlap)} evaluation rows overlap model-fitting rows; exclude the whole source study before evaluation")
    features = list(data["feature_names"])
    X = counts.loc[ids].reindex(columns=features, fill_value=0).astype(float)
    X = np.vstack([rankdata(row, method="average") / len(row) for row in X.values])
    return X, labels.loc[ids].astype(int).values


def scope(data, target):
    mask = training_mask(data, target)
    return {"source_n": int(mask.sum()), "excluded_source_rows": int((~mask).sum()),
            "evaluation": "source-study-excluded re-evaluation" if target in ("India/Mumbai", "Shanghai/related") else "external benchmark",
            "note": ("India/Mumbai shares PRJNA1240053 with the 50-row Indian source study; all Indian source rows are excluded before fitting." if target == "India/Mumbai" else
                     "PRJNA782768 and PRJNA910326 are deposited by the same Shanghai publication; all Shanghai source rows excluded. Participant independence is unresolved." if target == "Shanghai/related" else
                     "Previously inspected benchmark; exploratory.")}


BENCHMARKS = (("Portugal", "holdout"), ("Russia/Moscow", "holdout_664107"),
              ("Shanghai/related", "holdout_782768"))


def benchmark_scores(data, fitted, fit_related):
    """Different source fit for the related Shanghai benchmark, explicitly scoped."""
    results = {}
    for name, suffix in BENCHMARKS:
        current = fit_related() if name == "Shanghai/related" else fitted
        results[name] = {"y": np.asarray(data[f"y_{suffix}"]),
                         "scores": current.predict_proba(np.asarray(data[f"X_{suffix}"]))[:, 1],
                         "training_scope": scope(data, name)}
    return results
