#!/usr/bin/env python
"""Data contract for the Oralbiome hub site. Recomputes the cross-population T2DM
study's results LIVE from the pipeline (baseline reproduction + each cohort's
transfer AUC) and emits a multi-study site/results.json the dashboard + blog read.

Multi-study schema from the start so study #2 slots in without rework. Cohorts whose
interim counts are absent (e.g. a fresh clone) are skipped gracefully.

  .venv/bin/python scripts/build_site_data.py
"""
import hashlib, json, tomllib
from datetime import datetime, timezone
from pathlib import Path
from audited_data import load_data
import numpy as np, pandas as pd
from scipy.stats import rankdata
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from transfer_contract import external_rows, training_for_target, scope, benchmark_scores
from audited_data import provenance as eligibility_provenance, INPUTS

ROOT = Path(__file__).resolve().parents[1]              # study root: studies/cross-population-t2d
OUT = Path(__file__).resolve().parents[3] / "site" / "app" / "data" / "results.json"  # Remix app data
OUT.parent.mkdir(parents=True, exist_ok=True)

# curated cohort metadata (what the data alone doesn't carry)
COHORTS = [
    # id, label, population, country, specimen, kind
    ("portugal",     "Portugal",     "European",       "Portugal",     "saliva", "geographic holdout"),
    ("india",        "India/Mumbai", "South Asian",    "India",        "plaque", "new cohort"),
    ("mexico",       "Mexico",       "Latin American", "Mexico",       "saliva", "new cohort"),
    ("south_africa", "South Africa", "African",        "South Africa", "plaque", "new cohort"),
]
NEW_COHORT_FILES = {  # id -> (counts, labels)
    "india":        ("data/interim/india_genus_counts.csv", "data/raw/india_mumbai/labels.tsv"),
    "mexico":       ("data/interim/mexico_genus_counts.csv", "data/raw/mexico/labels.tsv"),
    "south_africa": ("data/interim/sa_genus_counts.csv",     "data/raw/south_africa/labels.tsv"),
}
GEO = {  # (lng, lat) for the world map
    "portugal": (-8.2, 39.4), "india": (72.9, 19.1),
    "mexico": (-102.5, 23.6), "south_africa": (22.9, -30.6),
}
CITES = {  # accession + short reference per cohort (data provenance)
    "portugal":     ("PRJNA679485",  "Almeida-Santos et al., 2021"),
    "india":        ("PRJNA1240053", "Bhosale et al., Diseases 2026"),
    "mexico":       ("PRJNA1208116", "Martinez-Gregorio et al., J Appl Microbiol 2026"),
    "south_africa": ("PRJNA723337",  "Matsha et al., J Dent Res 2020"),
}
TRAINING_REGIONS = [  # where the pooled model learned (context on the map)
    {"name": "NHANES (US)", "lng": -98.6, "lat": 39.8},
    {"name": "China", "lng": 113.0, "lat": 33.0},
    {"name": "India (withheld for Mumbai)", "lng": 77.0, "lat": 23.0},
]

def cb():
    return CatBoostClassifier(iterations=200, depth=4, learning_rate=0.1,
                              auto_class_weights="Balanced", random_state=42, verbose=0,
                              allow_writing_files=False, thread_count=4)

def within_cv(X, y):
    """5-fold CV AUC of a model trained + tested inside the cohort (in the model's feature space)."""
    if len(y) < 20 or y.sum() < 5 or (y == 0).sum() < 5:
        return None
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof = cross_val_predict(cb(), X, y, cv=skf, method="predict_proba", n_jobs=1)[:, 1]
    return round(float(roc_auc_score(y, oof)), 3)

def auc_ci(y, scores, n_boot=10_000, seed=42):
    """Stratified nonparametric 95% bootstrap CI for a fixed test-set AUC.

    Cases and controls are resampled separately so every replicate contains both
    classes. The seed makes the published data contract byte-stable apart from its
    generation timestamp.
    """
    y, scores = np.asarray(y), np.asarray(scores)
    pos, neg = scores[y == 1], scores[y == 0]
    if not len(pos) or not len(neg):
        return None
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        p = rng.choice(pos, len(pos), replace=True)
        n = rng.choice(neg, len(neg), replace=True)
        delta = p[:, None] - n[None, :]
        boot[i] = np.mean((delta > 0) + 0.5 * (delta == 0))
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return [round(float(lo), 3), round(float(hi), 3)]

def chance_relation(ci):
    """Classify evidence relative to chance without over-reading an AUC point estimate."""
    if ci is None:
        return "unknown"
    if ci[1] < 0.5:
        return "below"
    if ci[0] > 0.5:
        return "above"
    return "uncertain"

def transfer_auc(model, feats, counts_path, labels_path, data, name):
    counts_path, labels_path = ROOT / counts_path, ROOT / labels_path
    if not counts_path.exists() or not labels_path.exists():
        raise FileNotFoundError(f"Required transfer input is missing: {counts_path if not counts_path.exists() else labels_path}")
    X, y = external_rows(data, name, counts_path, labels_path)
    if name == "India/Mumbai":
        source_X, source_y = training_for_target(data, name)
        model = cb().fit(source_X, source_y)
    scores = model.predict_proba(X)[:, 1]
    ci = auc_ci(y, scores)
    return {"auc": round(float(roc_auc_score(y, scores)), 3), "auc_ci95": ci,
            "relation_to_chance": chance_relation(ci),
            "n": int(len(y)), "n_diabetic": int(y.sum()), "n_control": int((y == 0).sum()),
            "within_auc": within_cv(X, y), "training_scope": scope(data, name)}

def load_marker_panel():
    """Experiment #2 output (scripts/experiment_marker_stability.py), embedded lean:
    the heatmap subset + robust/flipper names + summary, not all 139 genus rows.
    Absent on a fresh clone before the experiment is run; the study omits it then."""
    p = ROOT / "data" / "processed" / "marker_panel.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return {k: d[k] for k in ("cohorts", "cohort_meta", "heatmap", "robust_up",
                              "robust_down", "flippers", "summary") if k in d}

def load_portability():
    """Experiment #3 output (scripts/experiment_portability.py): leakage-free LOCO
    stable-restricted vs full transfer + the Atopobium ablation. Absent on a fresh
    clone before the experiment is run."""
    p = ROOT / "data" / "processed" / "portability.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_sign_adaptation():
    """Experiment #4 output (scripts/experiment_sign_adaptation.py): few-shot
    per-population calibration curves (AUC vs local labels) + coefficient sign flips."""
    p = ROOT / "data" / "processed" / "sign_adaptation.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_ood():
    """Experiment #5 output (scripts/experiment_ood_detection.py): label-free OOD
    scores per cohort and whether they flag the reversed population."""
    p = ROOT / "data" / "processed" / "ood_detection.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_marker_properties():
    """Experiment #6 output (scripts/experiment_marker_properties.py): genus
    prevalence/abundance vs stability class."""
    p = ROOT / "data" / "processed" / "marker_properties.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_diversity():
    """Experiment #7 output (scripts/experiment_diversity_transfer.py): diversity
    vs taxonomic transfer per cohort."""
    p = ROOT / "data" / "processed" / "diversity_transfer.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_pop_vs_study():
    """Experiment #8 output (scripts/experiment_population_vs_study.py): within-China
    vs cross-population direction agreement (population vs study/batch decomposition)."""
    p = ROOT / "data" / "processed" / "population_vs_study.json"
    return json.loads(p.read_text()) if p.exists() else None

def load_roadmap():
    with open(Path(__file__).resolve().parents[3] / "commandem.toml", "rb") as f:  # repo-root contract
        d = tomllib.load(f)
    campaigns = d.get("campaign", d.get("milestone", []))
    return [{"title": m["title"], "status": m["status"], "why": m.get("why", "")} for m in campaigns]


def load_validation():
    records, hashes = {}, {}
    for name in ("panel", "calibration", "permutation", "subgroups"):
        relative = f"data/processed/validation_{name}.json"
        raw = (ROOT / relative).read_bytes()
        records[name] = json.loads(raw)
        hashes[relative] = hashlib.sha256(raw).hexdigest()
    panel, cal, perm = [records[n] for n in ("panel", "calibration", "permutation")]
    down = panel["downsample_reconstruction"]
    return {"status": "retrospective reconstruction; external benchmarks exploratory",
            "artifacts_sha256": hashes, "details": "/validation.json",
            "panel": {"nested_loso_macro_auc": panel["nested_loso"]["macro_auc"],
                      "selected_k": panel["source_selection"]["selected_k"],
                      "external": panel["external_benchmarks"],
                      "seed_count": down["n_seeds"], "panel_seed_mean": down["panel30"]["mean"],
                      "full_seed_mean": down["full"]["mean"], "panel_seed_wins": down["panel_wins"]},
            "calibration": {"source": {k: cal["source_oof"][k] for k in ("raw", "calibrated")},
                            "external": cal["external_benchmarks"]},
            "permutation": {k: perm[k] for k in ("observed_auc", "null_mean", "p_value", "n_permutations")},
            "subgroups": records["subgroups"]["subgroups"]}

def main():
    d = load_data()
    feats = list(d["feature_names"])
    Xtr, ytr = np.asarray(d["X_train"]), np.asarray(d["y_train"])

    # reproduction (baseline)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof = cross_val_predict(cb(), Xtr, ytr, cv=skf, method="predict_proba", n_jobs=1)[:, 1]
    cv_auc = round(float(roc_auc_score(ytr, oof)), 3)
    model = cb().fit(Xtr, ytr)
    port = round(float(roc_auc_score(d["y_holdout"], model.predict_proba(d["X_holdout"])[:, 1])), 3)
    benchmarks = benchmark_scores(d, model, lambda: cb().fit(*training_for_target(d, 'Shanghai/related')))
    allh = round(float(roc_auc_score(np.concatenate([r['y'] for r in benchmarks.values()]),
                                   np.concatenate([r['scores'] for r in benchmarks.values()]))), 3)

    marker_panel = load_marker_panel()
    portability = load_portability()
    sign_adaptation = load_sign_adaptation()
    ood = load_ood()
    marker_properties = load_marker_properties()
    diversity = load_diversity()
    pop_vs_study = load_pop_vs_study()

    validation = load_validation()
    targets = {"cv": round(validation['permutation']['observed_auc'], 3),
               "portugal": round(validation['panel']['external']['Portugal']['full_auc'], 3),
               "holdout3": round(validation['panel']['external']['three_cohort_pooled']['full_auc'], 3)}
    tolerance = 0.003
    reproduced = {"cv": cv_auc, "portugal": port, "holdout3": allh}
    repro_checks = {k: abs(reproduced[k] - target) <= tolerance for k, target in targets.items()}

    # leaderboard = transfer AUC per cohort (the flagship visual)
    labels_by_id = {row[0]: row[1] for row in COHORTS}
    ext = {cid: transfer_auc(model, feats, *paths, d, labels_by_id[cid]) for cid, paths in NEW_COHORT_FILES.items()}
    lb = []
    for cid, label, pop, country, spec, kind in COHORTS:
        if cid == "portugal":
            yh = np.asarray(d["y_holdout"])
            scores = model.predict_proba(np.asarray(d["X_holdout"]))[:, 1]
            ci = auc_ci(yh, scores)
            r = {"auc": port, "n": int(len(yh)), "n_diabetic": int(yh.sum()), "n_control": int((yh == 0).sum()),
                 "within_auc": within_cv(np.asarray(d["X_holdout"]), yh), "auc_ci95": ci,
                 "relation_to_chance": chance_relation(ci)}
        else:
            r = ext.get(cid)
            if r is None: continue
        lb.append({"cohort": label, "population": pop, "country": country, "specimen": spec,
                   "kind": "source-study-excluded re-evaluation" if cid == "india" else kind,
                   "training_scope": r.get("training_scope", scope(d, label)), "auc": r["auc"], "n": r["n"],
                   "n_diabetic": r.get("n_diabetic"), "n_control": r.get("n_control"),
                   "within_auc": r.get("within_auc"),
                   "auc_ci95": r.get("auc_ci95"),
                   "relation_to_chance": r.get("relation_to_chance", "unknown"),
                   "lng": GEO[cid][0], "lat": GEO[cid][1],
                   "accession": CITES[cid][0], "ref": CITES[cid][1],
                   "inverted": r["auc"] < 0.5})
    lb.sort(key=lambda x: -x["auc"])
    artifacts = {}
    for path in sorted((ROOT / 'data/processed').glob('validation_*.json')):
        record = json.loads(path.read_text())
        if record.get('eligibility') != eligibility_provenance():
            raise ValueError(f'Stale eligibility: {path.name}')
        artifacts[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('marker_panel', 'portability', 'sign_adaptation', 'ood_detection', 'marker_properties', 'diversity_transfer', 'population_vs_study'):
        path = ROOT / f'data/processed/{name}.json'
        record = json.loads(path.read_text())
        recorded = record.get('provenance', {})
        if any(recorded.get(k) != v for k, v in eligibility_provenance().items()):
            raise ValueError(f'Stale experiment: {name}; rerun with oral-only eligibility')
        script = 'marker_stability' if name == 'marker_panel' else name
        code = ROOT / f'scripts/experiment_{script}.py'
        if recorded['script_sha256'] != hashlib.sha256(code.read_bytes()).hexdigest():
            raise ValueError(f'Stale experiment code: {name}')
        artifacts[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        artifacts[str(code.relative_to(ROOT))] = hashlib.sha256(code.read_bytes()).hexdigest()
    for relative in ('scripts/audited_data.py', 'scripts/transfer_contract.py', 'scripts/reconstruct_validation.py',
                     'scripts/reconstruct_subgroups.py', 'data/models/processed_data_vsearch.pkl',
                     'data/processed/china_shanghai_t2dm_metadata.csv', 'data/processed/nhanes_demographics.csv'):
        artifacts[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    for relative in INPUTS + ['scripts/calibrate.py', 'data/models/global_logistic.json']:
        artifacts[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    sa_row = next(r for r in lb if r['cohort'] == 'South Africa')

    doc = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experiment_count": (ROOT / "docs" / "Experiments_Log.md").read_text().count("\n## "),
        "hub": {"name": "Oralbiome", "url": "https://oralbiome.scarpelli.ai",
                "tagline": "Oral-microbiome research. Testing what carries across studies."},
        "studies": [{
            "id": "cross-population-t2d",
            "title": "Cross-population oral-microbiome T2DM screening",
            "status": "active",
            "flagship": True,
            "paper": {"title": "Oral Microbiome Models for Type 2 Diabetes: A Retrospective Audit of Cross-Study Transfer",
                      "authors": "Scarpelli & Akhter, 2026", "pdf": "/preprint.pdf"},
            "key_finding": (f"Oral-only reconstruction: {len(ytr):,} source rows after excluding 129 fecal samples. "
                            f"South Africa transfer AUC {sa_row['auc']:.3f}, with an interval including chance, versus within-cohort {sa_row['within_auc']:.3f}. "
                            "India and the related Shanghai benchmark exclude their entire corresponding source study. "
                            "Association directions vary within and between countries; causes are not identified. "
                            "All external benchmarks remain exploratory, not untouched validation or a clinical screening tool."),
            "reproduces": {"cv_auc": cv_auc, "portugal_auc": port, "holdout3_auc": allh,
                           "targets": targets, "tolerance": tolerance, "checks": repro_checks,
                           "status": "pass" if all(repro_checks.values()) else "check"},
            "uncertainty": {"method": "stratified nonparametric bootstrap",
                            "confidence": 0.95, "resamples": 10_000, "seed": 42},
            "validation": validation,
            "eligibility": d['eligibility'], "artifact_manifest": artifacts,
            "related_benchmarks": [{"cohort": name, "n": len(r['y']), "auc": round(float(roc_auc_score(r['y'], r['scores'])), 3),
                                    "training_scope": r['training_scope']} for name, r in benchmarks.items()],
            "leaderboard": lb,
            "marker_panel": marker_panel,
            "portability": portability,
            "sign_adaptation": sign_adaptation,
            "ood_detection": ood,
            "marker_properties": marker_properties,
            "diversity_transfer": diversity,
            "population_vs_study": pop_vs_study,
        }],
        "roadmap": load_roadmap(),
        "training_regions": TRAINING_REGIONS,
    }
    payload = json.dumps(doc, indent=2) + "\n"
    OUT.write_text(payload)
    (OUT.parents[2] / "public" / "results.json").write_text(payload)  # served at /results.json
    # make site/ self-contained for deploy: copy the research log in as the blog source
    (OUT.parent / "research-log.md").write_text((ROOT / "docs" / "Experiments_Log.md").read_text())
    # bundle the preprint PDF for download from the site (if rendered)
    pdf = ROOT / "docs" / "Preprint.pdf"
    if pdf.exists():
        (OUT.parents[2] / "public" / "preprint.pdf").write_bytes(pdf.read_bytes())
    # sitemap with a real lastmod (crawlers can see freshness; regenerated per data build)
    (OUT.parents[2] / "public" / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url>\n'
        '    <loc>https://oralbiome.scarpelli.ai/</loc>\n'
        f'    <lastmod>{datetime.now(timezone.utc).date().isoformat()}</lastmod>\n'
        '    <changefreq>weekly</changefreq>\n'
        '    <priority>1.0</priority>\n'
        '  </url>\n'
        '</urlset>\n')
    print(f"WROTE {OUT}")
    print(f"  reproduces: CV {cv_auc} | Portugal {port} | 3-cohort {allh}")
    print("  leaderboard:")
    for r in lb:
        print(f"    {r['cohort']:14s} {r['population']:14s} {r['specimen']:6s} AUC={r['auc']}"
              + ("  <- INVERTED" if r["inverted"] else ""))

if __name__ == "__main__":
    main()
