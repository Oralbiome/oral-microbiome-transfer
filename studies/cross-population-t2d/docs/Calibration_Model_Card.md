# Research model card: local score adaptation

This is a research reference, not a clinical screening tool or calibrated disease-risk model. Current artifacts supersede historical mixed-specimen scores.

## Global fit and input scope

scripts/calibrate.py export fits balanced logistic regression (C=1) on 10,228 oral-only source rows: NHANES, four Chinese studies, and an Indian 50-row subset; 1,251 cases and 8,977 controls. Its target mixes NHANES self-reported diabetes with deposited clinical diabetes labels; a uniformly adjudicated T2D subtype is not established. It retains the historical 139-genus vocabulary and average-rank/139 transformation. SRA counts and NHANES public-use DADA2 tables differ in processing. Missing genera are filled with zero; nonfinite/negative counts are rejected. Unsupported assay/specimen substitutions are out of scope.

Local prior-regularized logistic fitting uses lambda=2 and disjoint labeled adaptation/evaluation samples. This changes a score, not proof of destination prevalence calibration. Counts overlapping the global source are rejected in adaptation and evaluation. In particular, do not evaluate the all-source global artifact on India/Mumbai. The experiment runner fits a separate model excluding the entire Indian source study.

## Corrected worked example

South Africa (88 specimens), repeated five-fold local evaluation across 12 correlated seeds:

| Local labels | Logistic AUC |
|---|---:|
| 0 | 0.304 |
| 5 | 0.352 |
| 10 | 0.388 |
| 20 | 0.472 |
| 40 | 0.615 |
| Separate within-cohort logistic reference | 0.859 |

These are not CatBoost leaderboard scores (corrected CatBoost 0.449, interval 0.323–0.578). Forty labels are nearly half the cohort; no optimal label requirement or independent replication is established. Fitting all local labels without separate evaluation is only a demonstration.

## Reproduce

```bash
python scripts/calibrate.py export
python scripts/calibrate.py demo
python scripts/calibrate.py calibrate --counts local_counts.csv --labels local_labels.tsv --out adapted.json
python scripts/calibrate.py predict --model adapted.json --counts new_counts.csv --out predictions.csv
```

A saved research score can be round-tripped but must not inform care. Calibrate and evaluate on independent participants, excluding any corresponding global source study. The standard CLI does not export arbitrary excluded-study global models; use the scoped experiment protocol.

## Limitations and harms

External cohorts and prior-strength choices were inspected during development. Row separation cannot undo adaptive reuse. No second independent African study was evaluated; no claim is made about exhaustive availability of such data. Labels, recruitment, treatment, specimens, and processing differ. Scores lack prospective threshold/utility validation. Missed cases could delay care; false positives could cause anxiety, unnecessary tests, cost, and unequal access burdens. Author agreement, reuse/ethics review, local risk calibration, and prospective decision analysis are required before any clinical framing. Publication is on hold and the repository remains private.
