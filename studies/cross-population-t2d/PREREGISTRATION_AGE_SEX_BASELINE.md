# NHANES age/sex-only baseline

Written 2026-11-17, before any model was fitted for this analysis. Owner approved
the analysis on 2026-11-17. This is exploratory, a single analysis, and uses
self-reported diabetes (DIQ010) labels, not confirmed Type 2 diabetes.

## Trigger and question

The manuscript limitations state that within NHANES, AUCs inside age strata
(0.576-0.608, Table 4) are lower than inside sex strata (0.689/0.707), so a
substantial part of NHANES discrimination may reflect age, and that no age/sex-only
baseline was fitted. The existing NHANES out-of-fold (OOF) AUC of the microbiome
model is 0.698 (`data/processed/validation_subgroups.json`, `overall`). Question:
does the microbiome add discrimination beyond age and sex in NHANES?

## Frozen design

**Population.** The NHANES rows of the audited oral matrix
(`scripts/audited_data.py::load_data`, 10,228 source rows, 1,251 cases), selected
exactly as `scripts/reconstruct_subgroups.py` does: study label equal to `nhanes`
(case-insensitive); SEQN taken from the sample index; age (`RIDAGEYR`) and sex
(`RIAGENDR`) joined from `data/processed/nhanes_demographics.csv`. Expected
n = 9,683 with 830 cases (from the stored subgroup file; the script asserts it from
code before fitting any model). Rows lacking age or sex: none expected; if any are
found the script aborts (no imputation, no silent dropping) and the design is
revised before any result is read.

**Folds.** Identical to the existing NHANES OOF analysis: pooled-source stratified
5-fold (`StratifiedKFold(5, shuffle=True, random_state=42)`) over all 10,228 rows,
stratified on the label, with NHANES rows scored when held out. The same fold
assignment is shared by every model (paired comparison). Non-NHANES rows have no
age/sex.

**Models** (all unweighted; NHANES survey weights are not used, matching the paper).
- **A, age+sex only.** Logistic regression (unpenalized), age as a restricted
  cubic spline with 4 knots at the 5th/35th/65th/95th percentiles (Harrell), plus
  sex. Knots are computed on the training NHANES rows of each fold only. Trained
  on NHANES training rows of each fold.
- **B, microbiome only.** The existing model reproduced through the same code path:
  CatBoost (`reconstruct_validation.PARAMS`, seed 42), pooled training on all
  training rows of each fold, 139 genus features.
- **C, microbiome + age + sex.** Same CatBoost config and pooled training as B with
  two appended features, age (years) and sex. Non-NHANES rows carry missing values
  for both (CatBoost native missing handling). This is a stated limitation: the
  missingness pattern also marks cohort, which B can already infer from taxa.
- **Sensitivity (secondary, reported, not decision-bearing):** B_nh and C_nh, the
  same as B and C but trained on NHANES training rows only.

**Primary endpoint.** AUC(A), and DeltaAUC = AUC(C) - AUC(A) with a paired stratified
bootstrap 95% CI (2,000 replicates, resampling cases and controls separately with
the same indices for all models, seed 42, percentile interval).

**Secondary (exploratory).** AUC(B) - AUC(A) paired CI; AUC of A, B, C within the
four age strata used by the manuscript (<40, 40-55, 55-65, 65+) and within sex.

## Decision rules (numeric, on DeltaAUC(C-A), 95% CI)
- lower bound > 0: "microbiome adds discrimination beyond age+sex in NHANES".
- CI includes 0: "no evidence microbiome adds beyond age+sex".
- upper bound < 0: "adding microbiome hurts".

Reading of B vs A: if the CI of AUC(B) - AUC(A) lies at or below 0 (upper bound
<= 0 or includes 0 with a point estimate <= 0) then microbiome-only discrimination
in NHANES is no better than age/sex alone; a lower bound > 0 means it is better.
CI-includes-0 with a positive point estimate is reported as inconclusive.

## Controls (all must pass before primaries are read; if any fails, stop, record
## the control results, fix the design, and do not read primaries)
- **C1 known-good.** Model B reproduces the published NHANES OOF AUC 0.698
  (0.6978) within +/-0.005. Failure means the pipeline is not the published one.
- **C2 known-bad.** Label permutation (fixed seeds; labels permuted over all
  10,228 rows, folds unchanged): mean NHANES AUC over 20 permutations of A and
  over 5 permutations of C lies in 0.47-0.53. The broken-design result is any mean
  outside that range.
- **C3 sensitivity.** A synthetic feature, label + Gaussian noise with separation
  tuned so its marginal AUC is about 0.75 (d = sqrt(2) * Phi^-1(0.75)), is added
  to model A. Its AUC must exceed AUC(A) with paired DeltaAUC lower bound > 0, and
  the augmented AUC must be at least 0.70. Failure means the pipeline cannot
  detect added signal.
- **C4 leakage guard.** For every fold assert train and test index sets are
  disjoint and cover all rows; age/sex spline knots are computed only on training
  rows (asserted by recomputing knots from the training rows and checking that
  test-row values never enter them; unit-tested).

## Reporting
Results are published whatever they are, including a negative or null verdict.
Single analysis with one primary; no multiplicity correction beyond that.
Caveats stated up front: self-reported labels; unweighted; conditional bootstrap
omits fold/seed variation; 95% interval from one fold split.
Outputs (new files only): `data/processed/baseline_age_sex_controls_v1.json`,
`data/processed/baseline_age_sex_v1.json`; code `scripts/baseline_age_sex.py`,
`tests/test_baseline_age_sex.py`.
