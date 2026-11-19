# REVISED PLAN v2 -- ADOPTED by the owner 2026-11-19; TAKES EFFECT when OSF Update 2 is approved. Not registered until then. No code changed.

**Status.** This file is the full text of a design-change revision (v2) of the registered plan `PREREGISTRATION_REANALYSIS.md` (OSF registration https://osf.io/6k82q/, DOI 10.17605/OSF.IO/6K82Q, registered plan SHA-256
`43c450568f510fa8427e4b3fae06ca7fb3edf7771d6a83a349cbd338a8716e24`, archived on OSF). The owner ADOPTED it on 2026-11-19 (decisions D1-D9 and E1-E8 as drafted, with one change: the K3 strong-positive gate level, D5, is set from the plan's own "material" band, see section 10, row K3).
It TAKES EFFECT only when OSF Update 2, which quotes this file's SHA-256 and cites its public location, is approved. Until then the registered plan and its failed sample validation (amendments entries 7 and 8) stay in force and nothing in this file changes any
criterion, band, seed or estimand. Even after the Update is approved the full run stays blocked until (a) the synthetic qualification of section 10 passes, (b) the new sample (v2) on permuted or synthetic labels passes, and (c) the owner creates the approval marker `osf/full_run_approval.json`. The reasons for every change, the evidence, and how each is
validated without real outcomes are in `drafts/DESIGN_CHANGE_PROPOSAL_v2_2026-11-19.md` (changes D1-D9, E1-E8); the changed text here is marked "(v2)" where it replaces registered text. A word-level difference against the registered plan is in `drafts/PREREGISTRATION_REANALYSIS_v2_vs_v1.worddiff.txt`.
**Anchoring.** This file is committed unchanged to the public repository https://github.com/Oralbiome/oral-microbiome-transfer (folder `preregistration/`; aggregate statistics only, no participant-level data) and its SHA-256 is quoted in OSF Update 2. The file must not change after that hash is quoted.

The registered plan's own text follows, revised. Section numbers are unchanged; new material is section 0B, section 0A addendum (0A-2), section 7 item "Reading a negative contrast", and the rewritten sections 2 (richness reporting), 3.6, 6, 10 and 12.

Standing results that this plan never replaces: the age/sex baseline (`PREREGISTRATION_AGE_SEX_BASELINE.md`,
`data/processed/baseline_age_sex_v1.json`: A 0.803, B 0.698, C-A = -0.0011, CI [-0.0093, 0.0072]) and every published number.
All OLD results stay on record as HISTORICAL (section 4).

## 0B. Why a v2 revision exists (v2; trigger, evidence, mechanism, change, confidence)

- **Trigger.** The section-10 sample validation of the registered plan was run on 2026-11-19 and failed SEVEN criteria: controls K2 (logistic), K3n (logistic), K3 (both learners), KA2, KA3 and KA4, and the sample timing criterion (`osf/sample_validation_record.json`,
  `data/processed/reanalysis_sample_v1/`, amendments entries 7 and 8). No criterion was relaxed and no setting was tuned.
- **Evidence and mechanism (graded; from two independent read-only reviews, `drafts/reviews/`).** PROVEN: the logistic Part B arm loses about 0.03 AUC under permuted labels (mean -0.0295 over 20 draws) because a uniformly penalized 284-column block, with a penalty chosen by inner
  log loss, cannot recover the nested age/sex model (pure Gaussian noise in place of the genus columns reproduced the loss in one draw: 0.7731 against 0.7729). PROVEN: CatBoost also has a negative null contrast (all 20 K2 deltas negative, mean -0.0037; 7 of 20 with a CI upper bound below 0),
  so the registered "harm" band fires on null data. PROVEN: the registered richness flag is raised when both models are at chance (KA3, 20/20) and silent when richness alone beats the primary model (Shandong: T3 0.839 against T2 K139 0.716). PROVEN by construction: KA2 and KA4 put synthetic labels on the
  target only, while T1/T2 are trained on source labels. PROVEN: K3's single draw delivered a pooled AUC of 0.570 rather than 0.60 and the K3 gate is underpowered at 0.60. SUGGESTIVE: study identity (Treponema detected in 0.000 of NHANES rows and 0.910 of the other source rows) can act as a proxy; thread oversubscription explains the timing failure.
- **Change.** The design changes D1-D9 and engineering fixes E1-E8 of the proposal are applied in the sections below. The Part A primary (T2 AUC per external cohort, decision words at 0.5), the Part B primary (DeltaAUC per learner, P0+M+Z minus P0), the bands 0.02/0.01, R = 20 fold seeds 1-20, the bootstrap seeds and sizes, and
  the registered hypotheses are UNCHANGED; the exceptions are named in the proposal (the richness hypothesis H-A2 and the word "harm").
- **Confidence limits.** Every v2 rule was written after seeing the failed sample's outputs and the reviews' probes (section 0A-2), so none is prospective with respect to that exposure; the rules are therefore validated on fresh synthetic seeds before any outcome-bearing run (section 10), and this does not make any Part A or Part B result confirmatory (section 5 still applies).

## S. Owner-confirmed settings

This table is the ONE place where the owner settings are listed. OC1-OC4 are owner-confirmed 2026-11-17 (the recommended defaults were accepted unchanged); the
rest of this text assumes them. Changing a setting is a one-line edit of its row PLUS the same value where the body cites the ID
(the body always cites the ID, for example "R (OC1)"); after any edit re-run `scripts/check_registration_manifest.py --write`
and update the plan hash in `osf/OSF_REGISTRATION_PACKET.md`.

| ID | Setting | Value (assumed below) | Alternative considered | Status |
|---|---|---|---|---|
| OC1 | Part B fold seeds R, and the decision bands | R = 20 fold seeds (1..20). Bands on the 95% CI [lo, hi] of DeltaAUC: material `lo >= 0.02`; small but real `0 < lo < 0.02`; no benefit `lo <= 0 and hi < 0.01`; inconclusive `lo <= 0 and hi >= 0.01`; below reference `hi < 0` (v2: this band was named "harm"; numbers unchanged, wording changed, section 7) | other R (at least 10) or other cutoffs; must be changed before registration, never after | owner-confirmed 2026-11-17; v2 wording change adopted by the owner 2026-11-19 (effective with OSF Update 2) |
| OC2 | Null for the within-stratum permutation diagnostic | Fixed configuration: for each learner and arm, the hyperparameters selected by inner tuning on the REAL labels at fold seed 1 are held fixed for all 200 permuted-label refits (about 0.7 h). Disclosed limitation: the configuration was tuned toward the real labels, so the null can only be slightly conservative | Full inner re-tuning per permutation (about +19 h, roughly 30x the cost) | owner-confirmed 2026-11-17 |
| OC3 | Baseline controls under the new hash binding | Re-run the baseline (A, B, C) controls into a NEW file `data/processed/baseline_age_sex_controls_v2.json` bound to current input, script, preregistration and control-schema hashes, as part of the sample-validation step (section 10), not now. `baseline_age_sex_controls_v1.json` is never overwritten. Purpose: the original A/C result becomes replayable under the Amendment-4 binding again | Do not re-run; the original A/C result stays reported, but is not replayable under the new binding (disclosed) | owner-confirmed 2026-11-17 |
| OC4 | OSF embargo | NO embargo: public on registration, because nothing in this plan is sensitive and an openly visible plan is more credible for an audit | Embargo up to four years (OSF maximum); the plan then becomes public automatically at the end date | owner-confirmed 2026-11-17 |
| OC5 | Per-author prior-knowledge statement (section 0A, last subsection) | Joint statement: both authors saw every item listed in section 0A | Stated by the corresponding author on 2026-11-18, on the basis of the second author's blanket sign-off and review of the work | Owner-confirmed 2026-11-18 |
| OC6 | Part A primary model | T2 (v2 genera + explicit detection count and depth), as drafted; T1 and T3 are secondary | T1 as primary | default as drafted; not among the four settings the owner confirmed |

## 0. Why this exists (trigger, evidence, mechanism, confidence)

- **Trigger.** An audit found that the 139-column rank matrix is not an abundance matrix: genera absent from a sample are
  zero-filled, then ranked, so every absent genus gets the same mid-rank `(Z+1)/(2*139)` with Z the sample's number of
  zero genera. Detection count Z (and through it sequencing depth) is encoded in 139 columns.
- **Evidence** (`drafts/ZERO_FILL_DIAGNOSIS_2026-11-17.md`, `drafts/*_2026-11-17.json`): exact reproduction of X from counts;
  absent-genus counts per cohort (India 63, Portugal 49, Shanghai 33, Mexico 30, Russia 27, SA 14); label-vs-Z correlations
  (SA +0.47, Shanghai +0.24, Mexico -0.18); holding fitted models fixed and neutralizing absent genera moves the six external
  transfer AUCs by 0.04-0.12; a one-feature detection-count model gets 0.791 within South Africa against 0.853 for the rank
  matrix; 38 of 58 published "flipper" genera are all-zero in at least one target cohort.
- **Mechanism.** Proven: the encoding (algebraic form + exact reproduction). Suggestive, NOT convicted: that detection count
  is what drives the South Africa reversal. Unknown: the artifact-free value of any transfer AUC, which needs a chosen
  representation and retrained models (this plan), not a swapped-in input.
- **Engineering status.** Protocol Amendment 4 (`PREREGISTRATION_TRANSFER_PROTOCOL.md`) repaired four assurance defects
  (non-finite QC passing, NaN scores producing a "reversal", incomplete controls accepted and bypassed, unbound baseline
  replay) and added a score-once ledger. It did NOT touch the representation. This draft is where that is decided.
- **Confidence limits of the whole plan.** All six external cohorts and NHANES informed development, so no result here is
  confirmatory (section 6). The new representation is itself a design choice made after seeing how the old one failed.

## 0A. Data already observed (disclosure; secondary-data plans are judged on this)

Every dataset used here already exists and has been analyzed by the authors. This section states what has been seen. It is
the answer to "prior knowledge of the data" in the OSF form. It describes what was seen as of 2026-11-17, before registration.

**Seen in full (the published v1 analysis, all six external cohorts and NHANES).**
- All v1 results exist and were generated with the six external cohorts visible during development of the estimator, K, vocabulary and
  every secondary analysis: source LOSO K30 macro AUC 0.684 (all-source selection; nested 0.661) against 0.669 for the full
  vocabulary, pooled source OOF 0.793 (NHANES-dominated); the six external transfer AUCs (for example Portugal 0.646, South Africa
  0.449 with CI 0.323-0.578); within-South-Africa 0.853; the 58 "flipper" genera, the Atopobium r = +0.47 in South Africa, the
  0.340 Atopobium ablation, the portability restriction; the NHANES age/sex baseline (A 0.803, B 0.698, C-A -0.0011).
- Consequence: no Part A or Part B result in this plan is confirmatory. This is stated again in section 5.

**Seen in the zero-fill diagnosis (`drafts/ZERO_FILL_DIAGNOSIS_2026-11-17.md`, read-only, before this plan).**
- The rank encoding of absent genera (algebraic form, exact reproduction from counts), absent-genus counts per cohort, label-versus-Z
  correlations (SA +0.47, Shanghai +0.24, Mexico -0.18), and the representation-sensitivity AUCs of section 4 (fixed fitted models, absent genera
  neutralized to the per-sample median or to NaN; for example SA 0.449 -> 0.529 / 0.386, India 0.569 -> 0.616 / 0.436, Mexico 0.611 -> 0.528 / 0.545).
- The within-cohort comparators (rank matrix 0.853 versus detection count alone 0.791 in South Africa; depth alone 0.706 in Mexico, 0.822 in Russia), the
  single-feature AUCs of Z as a score (0.526 Portugal ... 0.803 South Africa), the marker recompute (58 -> 40 flippers with absent genera excluded; 38 of 58
  all-zero in at least one cohort).
- The Part A representation (section 1) was designed AFTER this diagnosis, so its design choices are informed by those cohort-level results.

**Seen in probes by other agents (read as reported; not used as a prior, effect size or power input).**
- An external reviewer's stacked model reached 0.811 within NHANES; it is non-nested and leaky and is not used anywhere in this plan.
- A second reviewer's fold-matched within-stratum diagnostic: microbiome-only score B 0.576, age/sex score A exactly 0.500, plus the observation that
  CatBoost on age and sex alone gives 0.792 against 0.803 for logistic A (a learner mismatch of about 0.011 inside the earlier C-A contrast). The report file was held at
  `/tmp/oralbiome-audit/codex/SECOND_OPINION_2026-11-17.md`, which was not retained, so it is not pinned; its figures appear in the diagnosis and the NHANES follow-up draft, which are pinned.

**Seen for S1 (descriptive only, before any outcome-bearing fit).** For the 9,683 study rows joined on SEQN: BMXBMI missing in 76 rows (cases 10, controls 66; 2 rows
without a BMX record); SMQ020 missing in 1,681 rows, all aged 14-19 (cases 9, controls 1,672), none aged >= 20; SMQ020 code 9 in 2 rows; SMQ040 missing in 6,220 rows
(asked only if SMQ020 = 1; 0 missing among 3,463 asked; 2 coded 7). These label-conditional counts were seen; no model was fitted with BMI, smoking or RIDRETH1.

**NOT seen.** No v2 representation output of any kind, no T1/T2/T3 score, no repeated-seed Part B arm, no logistic or CatBoost fit including Z, BMI, smoking or race/ethnicity, no
K/KA control result, no sample-validation result, no baseline_age_sex_controls_v2. The authors have not looked at the labels of China/Shandong (`china_shandong_sun`) under any v2 model.

**Public prior dissemination.** A working manuscript with the v1 numbers is publicly hosted (`oralbiome.scarpelli.ai`) and archived as GitHub release v2026.11.17.2 of
`Oralbiome/oral-microbiome-transfer` (no Zenodo DOI exists yet), and cited by `CITATION.cff`. An interim correction notice about
the zero-fill finding was posted on 2026-11-17/18 (website, paper, repository README); this plan does not depend on it.

**Per-author prior knowledge (OC5).** Joint statement by the corresponding author (2026-11-18): both authors had seen every item listed above before this plan was
finalized. The first author (J. Scarpelli) directed the audit; the second author (A. Akhter) reviewed and approved the work.

## 0A-2. Data already observed, addendum (v2; as of 2026-11-19, after the failed sample validation)

Everything below was seen by the authors, or by agents working for them, AFTER the registered plan was frozen and BEFORE this revision was written. Nothing here was used as a prior, effect size or power input; the v2 rules were nevertheless written knowing it (section 0B, confidence limits).

**Seen: the failed sample validation outputs** (`data/processed/reanalysis_sample_v1/`, `osf/sample_validation_record.json`, amendments entries 7 and 8).
- **Real held-out Shandong v2 values** (`china_shandong_sun`, n = 130, 103 cases, 27 controls; AUC, 95% CI): T1 K30 0.6739 (0.5685-0.7728); T2 K30 0.7116 (0.6063-0.8073); T1 K139 0.8393 (0.7483-0.9177); T2 K139 0.7156 (0.6113-0.8123); T3 0.8389 (0.7663-0.9018); T2 K30 minus T3 -0.1273; T2 K139 minus T3 -0.1233.
  Sample values are not results and are not used for any decision, but they ARE seen, and the Shandong study is one of the six folds of the deferred K selection and source-side recheck.
- **Control results:** K2 (logistic mean DeltaAUC -0.0295; CatBoost -0.0037 with all 20 negative and 7 of 20 with CI upper bound below 0); K3 (achieved pooled feature AUC 0.570; logistic -0.031; CatBoost +0.0044, CI -0.0006 to +0.0094); K3n (logistic -0.0362; CatBoost -0.0027); K6 (content contrast logistic -0.0132, CatBoost -0.0052);
  KA2 (mean AUC up: v1 0.5935, T3 0.7479, T2 K30 0.5502, T2 K139 0.5400; down: 0.4358, 0.2660, 0.4540, 0.4944; old-rule hits 14/20 and 11/20); KA3 (T2 false-call 0.15 at K30 and 0.10 at K139; legacy flag 20/20 and 19/20); KA4 (T2 transfer 5/20 at K30, 2/20 at K139; legacy flag 15/20 and 14/20); timing (logistic P0+M+Z 1.41 s per fit against a 0.60 s ceiling).
- **The T2 K30 and K139 panels** (`treatment_delivered.json`, a source-trained SHAP ranking; Treponema is first in the K30 panel).

**Seen: the two reviews' probes** (`drafts/reviews/`; all on permuted-within-stratum or fully synthetic labels, no real outcome).
- **Fable:** the logistic table on one permuted draw (P0 0.8041; P0+M+Z at C = 1e-3, 1e-2, 1: 0.7848, 0.7729, 0.7602; P0 plus 280 Gaussian noise columns 0.7731; P0 unpenalized with ridge on M at C = 1e-5, 1e-4, 1e-3: 0.8038, 0.8015, 0.7908), the 300-seed K3 delivery distribution (mean pooled AUC 0.5995, SD 0.0105),
  the repaired controls on 8 draws (content rule T2 transfer 7/8 at K30 and 8/8 at K139; richness rule 8/8; two cells uninformative), the resampling-duplication finding (about 32 unique rows behind 88 resampled cases), the T3 inner-CV tuning on real source labels, and the study-identity table: Treponema detected in 0.000 of 9,683 NHANES rows and 0.910 of 545 other source rows, Butyrivibrio 0.001 and 0.783,
  Moryella 0.066 and 0.822, 6 of 139 genera with a detection-fraction difference of at least 0.5; all six external cohorts detect Treponema in 78-99% of rows; NHANES 8.6% cases against 53-84% in the other source studies; Shandong mean detection count 78.8 against 41.3 in NHANES.
- **Codex:** the logistic probe on permuted label seeds 1000 and 2000 (tuned AUCs P0 / P0+Z / P0+M+Z 0.80402 / 0.80304 / 0.77294 and 0.80414 / 0.80320 / 0.76721; C = 0.01 chosen in all ten folds; no-class-weight and C = 1e-4 variants), the age/sex-matched K3 AUCs (0.4825, 0.5320, 0.5832 at nominal 0.50, 0.55, 0.60) and the pooled ones (0.4686, 0.5190, 0.5700),
  the observations on KA2-KA4 clone rows, K4's pass expression, K5's noisy twin (0.48631) and K6's negative-contrast reading, and the row-handling observation (no-detection rows are scored in Part B).
- **Owner-requested D5 computation (2026-11-19; synthetic only, no real label):** the K3 gate level was computed from the plan's own material band on fresh synthetic seeds 7300000-7320999 (`drafts/d5_material_level/`): the injected-feature AUC at which the oracle incremental DeltaAUC over an age and sex baseline of AUC 0.800 is 0.02 is 0.638 (rounded to 0.64). Only aggregate numbers already in this plan (9,683 rows, 830 cases, baseline AUC about 0.80) were used as inputs.

**Seen: loader behavior.** The label-disabled external loader reads label files to keep rows with a recorded 0/1 label (amendment 8).

**Training on real source labels.** The failed sample trained T1/T2/T3 on the real labels of the source studies other than Shandong, NHANES included (10,098 fit rows), and tuned T3's C by inner log loss on them. No output of those inner losses was written. This follows amendment 2 and conflicts with the literal registered firewall wording (rewritten in section 10, v2).

**Still NOT seen.** No v2 model has been scored on any external cohort or on real NHANES labels (the evidence is stated in amendment 8); no v2 Part B arm has been fitted on real NHANES labels; no S1 fit; no real-label v2 K selection or source-side recheck; no qualification (section 10) result of any kind.

# PART A. Representation: presence-aware features

## 1. The representation rule (new, "v2")

Applies identically to source, external and NHANES rows. Counts are the raw per-sample genus counts mapped to the frozen
139-genus vocabulary exactly as `transfer_pipeline.map_taxonomy` (same exact-name mapping, ambiguity and QC rules).

1. **Detected set** D_i = vocabulary genera with count > 0 in sample i. Detection count `nd_i = |D_i|`. (Count > 0 is
   depth-sensitive; that is why depth is an explicit covariate below. A count >= 2 threshold is NOT a primary and is listed as a limitation.)
2. **Rank only among detected genera.** For g in D_i: `r_ig = average_rank(count_ig among D_i) / nd_i`, in (0, 1]. Ties get the
   average rank. A sample with `nd_i = 0` is ineligible (already excluded by the read-floor rule; the 37 source rows
   with nd = 0, which include the 20 zero-total rows, are handled by section 3.6 (v2)).
3. **Absent vocabulary genera are missing, not ranked:**
   - **CatBoost:** `r_ig = NaN` with `nan_mode = "Min"` pinned explicitly (CatBoost's default; pinned so a library
     default cannot change it silently). Trees can still split on "missing"; that per-genus presence information is
     intended and is why richness is also measured explicitly (item 4).
   - **Logistic (L2):** `r_ig = 0` for absent genera (strictly below every observed rank) PLUS an explicit presence indicator
     `p_ig in {0,1}` for each genus (278 columns). Standardization on training rows only.
4. **Explicit covariates, always present in the "+Z" arms:** detection count `nd_i` and depth `log10(total reads_i)`, where
   total reads is the sample's sum over ALL taxa in its count table (not only the vocabulary), `>0` by eligibility. Depth is
   pipeline-dependent (NHANES DADA2 table vs SRA/VSEARCH cohorts), so it is not comparable across studies; this is why Z is
   reported as a comparator (section 2), not interpreted as biology.

The old rule is retained in code as `representation="v1_zero_fill_rank"` (bit-identical to the pinned v1 path) so the
known-good control (section 8, KA1) can run it. The v2 rule is a new module and a new protocol version
(`transfer_protocol_v2`), never an in-place edit of v1 (which stays pinned, with Amendment 4 history).

## 2. Models and the primary endpoint per external cohort

Training: all audited source rows (NHANES + the five clinical source studies, as v1). Estimator family and seed as v1
(`reconstruct_validation.PARAMS`, seed 42; logistic L2 with C from a fixed grid by inner log loss). Panel selection by the
same source-only rule: mean |SHAP| ranking on source rows, K in {30, 139} chosen by macro leave-one-source-study-out AUC (ties go
to 139), recomputed under v2. Z features (`nd`, `depth`) are not subject to panel selection (always included in T2).

Three transfer models per external cohort, trained once on source rows only and scored on the target without refit:
- **T2 (primary): v2 genera + Z.** The "new rule" model.
- **T1 (secondary): v2 genera, no explicit Z** (shows what NaN-pattern leakage alone carries).
- **T3 (comparator): detection count + depth only**, logistic regression on `(nd, log10 depth)`, trained on the same source rows
  and transferred identically (no per-cohort standardization), so a "transfer" that is just richness is visible.

**Primary per external cohort: the AUC of T2 against the binary label, with the same CI method** (stratified percentile
bootstrap, 10,000 replicates, seed 20261117, 95%) and the same decision words (transfer / reversal / inconclusive at 0.5).
**Richness reporting (v2; replaces the registered "richness flag").** The registered flag (difference CI includes 0, or T3 informative with T2 inside T3's CI) is retired as an interpretation: it fires when both models are at chance and stays silent when T3 beats T2 (amendment 7, KA3 and the Shandong sample).
It may still be printed as "legacy flag" for continuity and is never interpreted. For every external cohort and each K in {30, 139} the report states, in this order, with the same stratified bootstrap (10,000 replicates, seed 20261117, 95%) and identical resamples:

1. **T2's result:** AUC, CI and decision word (transfer / reversal / inconclusive at 0.5). This remains the primary.
2. **T3's result and direction:** AUC, CI and decision word of the detection-count-and-depth score. T3 is a fixed monotone score with its sign learned on source rows, so "transfer" means T3 points the way it did in the source and "reversal" means it points the opposite way. T3 is *informative* when its decision word is transfer or reversal.
3. **A paired, direction-aware difference.** Let the orientation o be +1 if the T3 point estimate is at least 0.5 and -1 otherwise (fixed from the full sample and held fixed in every replicate, never re-derived per replicate). Oriented AUC is a(M) = AUC(M) if o = +1 and 1 - AUC(M) if o = -1, for M in {T2, T3}.
   The difference is D = a(T2) - a(T3), with a paired bootstrap CI [dlo, dhi]. The practical margin is m = 0.05 AUC (a choice: about half of the typical 95% half-width of 0.1 at the cohort sizes of 46-88; stated as a limitation: differences below m are not resolvable in these cohorts). Report D only when T3 is informative; when T3 is not informative report the unoriented difference with the label "T3 uninformative".
   Statements, mutually exclusive, in this priority: "T2 exceeds richness" if dlo is greater than +m; "T2 below richness" if dhi is less than -m; "T2 comparable to richness" if dlo is greater than -m and dhi is less than +m; otherwise "difference not resolved".

The report must print one line per cohort and K, never a flag, using the table below. The cases where T3 is informative and T2 is inconclusive, reversed or worse are stated explicitly, because that is the case in which a richness-only reading beats the primary model.

| T2 result | T3 result | Required statement |
|---|---|---|
| transfer | uninformative | "T2 transfers; richness and depth alone do not (T3 uninformative)" |
| transfer | informative | the D statement above ("exceeds", "comparable", "below" or "not resolved") |
| inconclusive | informative | "T3 informative (direction stated); T2 inconclusive" plus the D statement; never "richness-compatible T2" |
| inconclusive | uninformative | "neither model resolved" |
| reversal | informative | "T2 reversed; T3 informative (direction stated)" plus the D statement |
| reversal | uninformative | "T2 reversed; T3 uninformative" |

The wording "richness-compatible" is allowed only when T3 is informative and the statement is "T2 comparable to richness"; it does not identify mediation and does not say how much of T2 uses richness. The report is never allowed to replace the T2 decision word.

Eligibility and evaluation go through `transfer_pipeline.evaluate_cohort` (Amendment 4: verification, score-once ledger,
non-finite refusal). The score-once ledger records a v2 cohort ID distinct from any v1 ID; v1 IDs that were never scored stay unscored.

## 3. Recomputation under the new rule

Everything below is recomputed from raw counts with v2 and written to NEW files (suffix `_v2`); no tracked v1 result file is
overwritten.

1. **Transfer AUCs.** Six external cohorts (Portugal, Russia/Moscow, Shanghai/related, India/Mumbai, Mexico, South Africa), T1/T2/T3
   as in section 2, full vocabulary and K = 30 panel variants (the old tables report both), with CIs.
2. **Marker stability.** Per genus and cohort, a genus is *testable* only if detected in at least 20 samples with at least 5 in each
   class. For testable genera compute two statistics: point-biserial of the presence indicator with the label, and
   point-biserial of the v2 rank among samples where detected (needs 20 detected). Sign-flip versus NHANES uses the old
   `|r| >= 0.15` threshold on the unrounded values. Untestable genera are reported as UNTESTABLE, never as flips or as stable.
   Reported: counts of stable / flipper / untestable, the old counts beside them, and the fraction of old flippers that are
   untestable (diagnosis: 38 of 58 are all-zero in at least one cohort).
3. **Portability (stable-restricted).** Leave-one-cohort-out as the old experiment but with the v2 representation and the new
   testable-stable set built from the other cohorts only; the Atopobium ablation is retained only where Atopobium is
   testable in the target (it is all-zero in Portugal, India and SA, so it is reported "not applicable" there).
4. **Within-cohort.** Same 5-fold seed-42 CV and the comparators of the diagnosis (v2 matrix + Z, v2 matrix without Z, detection
   count only, log depth only, count + depth), plus the v1 matrix for continuity. Report within-cohort and transfer
   side by side; no CIs from a single 5-fold run (repeat 5 times with different fold seeds and report the range).
5. **Sign adaptation, OOD detection, population-versus-study, feature reversal, India-in-pool, diversity.** Recomputed with
   v2 where they used ranks (diversity-from-counts already does not); these are descriptive/exploratory and only the portability
   and marker numbers feed any claim.
6. **Sensitivity: rows with no detected vocabulary genus (v2; reconciles amendment 5).** Two sets are distinct: the 20 zero-total source rows (17 NHANES, 3 Shanghai; no reads at all) and the 37 source rows with `nd = 0` (33 NHANES, 4 Shanghai), which contain the 20 plus 17 rows that have reads but none in the 139-genus vocabulary.
   All 37 stay in the primary training fit for continuity with v1 (all-NaN genus features for CatBoost, rank 0 and indicator 0 for logistic, `nd = 0`, depth = log10 of the total reads, and 0 for the 20 zero-total rows only, because log10 of zero is undefined). The sensitivity excludes all 37 from fitting AND, in Part B, from scoring (section 6), and both are reported.
   Populations by use: **Part A fitting (primary)** all 10,228 audited source rows minus the held-out study; **Part A scored rows** only rows of an eligible external cohort (the read-floor eligibility already excludes zero-total rows; any `nd = 0` row that passes it is a scored row and is reported by SEQN/ID);
   **Part B primary** all 9,683 NHANES rows are both fitted and scored, including the 33 `nd = 0` rows (no silent dropping); **Part B sensitivity S2** (new, secondary) excludes the 33 rows from fitting and scoring in both arms of the primary contrast; **synthetic controls** exclude `nd = 0` rows from every synthetic target and list them.
7. **Source-side recheck.** The six-study LOSO K30 macro AUC and the pooled OOF AUC are recomputed under v2 and reported next to
   the old 0.684 / 0.698 so the reader sees whether the headline source performance survives.

8. **Study-identity sensitivity (v2, new; secondary, label-free).** Define the *identity genera* label-free from source rows only: genera whose detection fraction (count greater than 0) in the NHANES source rows differs by at least 0.5 from its detection fraction in the other five source studies pooled.
   (On the pinned data this is 6 of 139 genera, including Treponema: 0.000 of 9,683 NHANES rows against 0.910 of 545 other source rows; Butyrivibrio 0.001 against 0.783; Moryella 0.066 against 0.822.) NHANES uses a different upstream pipeline (public DADA2 tables against the VSEARCH pipeline used for the other cohorts), and NHANES is 8.6% cases against 53-84% in the five other source studies, so an identity genus can encode study
   membership. The set is computed and listed once, before any outcome-bearing run, and never recomputed from outcomes. Report: (a) the share of mean |SHAP| (the same 1,024-row source sample, seed 42) carried by the identity genera for T1/T2 at each K; (b) all section 3.1 transfer AUCs re-fit with the identity genera removed from the vocabulary (T1, T2, T3 unchanged for T3);
   (c) T1/T2 trained WITHOUT the NHANES rows (the five clinical source studies only). These are secondary and never replace the primary. A material move of a transfer AUC (more than m = 0.05 in either direction) is reported as "identity-sensitive".

## 4. Historical results and the representation-sensitivity table

All old numbers stay in the record, labelled **HISTORICAL (v1 zero-fill rank representation; representation-dependent)** wherever
they are quoted, with the table below beside them. They are not corrected estimates: they hold the fitted models fixed and
change only how absent genera are represented, so they measure dependence, not the right answer (source:
`drafts/ZERO_FILL_DIAGNOSIS_2026-11-17.md` section 2; frozen-panel and all-source-fit variants there).

| Cohort | n (cases) | Absent of 139 | corr(label, Z) | Full model AUC: orig / median / NaN | Panel-30 AUC: orig / median / NaN |
|---|---|---|---|---|---|
| Portugal | 50 (25) | 49 | -0.065 | 0.646 / 0.662 / 0.578 | 0.578 / 0.694 / 0.669 |
| Russia/Moscow | 46 (15) | 27 | +0.107 | 0.639 / 0.718 / 0.714 | 0.662 / 0.622 / 0.602 |
| Shanghai/related | 80 (40) | 33 | +0.244 | 0.546 / 0.589 / 0.587 | 0.609 / 0.581 / 0.578 |
| India/Mumbai | 60 (40) | 63 | +0.149 | 0.569 / 0.616 / 0.436 | 0.541 / 0.665 / 0.604 |
| Mexico | 87 (41) | 30 | -0.181 | 0.611 / 0.528 / 0.545 | 0.571 / 0.459 / 0.459 |
| South Africa | 88 (57) | 14 | +0.467 | 0.449 / 0.529 / 0.386 | 0.491 / 0.614 / 0.497 |

The old results (including the South Africa 0.449 "reversal", the flipper count 58, the Atopobium r = +0.47, the 0.340 ablation
and the within-SA 0.853) are reported as historical and as not interpretable as organism-level evidence. They are not deleted
or edited in place.

## 5. Multiplicity

No new primaries beyond one per external cohort (T2 AUC, section 2). The richness report (section 2), T1, T3, K = 139 vs 30, marker, portability and
within-cohort results are secondary/descriptive and unadjusted. Because every cohort informed development (the six external cohorts
were visible while the v1 estimator, K and vocabulary were chosen, and while the defect was found), **every Part A result is labelled
EXPLORATORY**, whatever its interval. Any pooled "transfers across cohorts" claim needs Bonferroni over the cohorts scored (CI level
`1 - 0.05/m`), as in the v1 protocol. A confirmatory test needs a NEW cohort that passes the v1 eligibility floor (>= 88 cases,
>= 88 controls, Hanley-McNeil half-width <= 0.0703).

# PART B. NHANES incremental value (design carried forward)

## 6. Question, population and design

Does the oral microbiome add discrimination for **self-reported** diabetes (DIQ010; not adjudicated T2D) beyond demographics in
NHANES 2009-2012, learner-matched and nested, and how much of any gain is microbial content as opposed to richness/depth?
(Trigger and audit context: `PREREGISTRATION_NHANES_FOLLOWUP_DRAFT.md` section 1.) Population exactly as
`baseline_age_sex.py::setup` (n = 9,683, 830 cases, asserted; no silent dropping in the primary). NHANES-only training for all arms.
Stratified 5-fold outer CV on the label, repeated over **R fold seeds** (OC1; default R = 20, seeds 1..20), identical folds across arms within a seed,
fold assignments hashed. Everything (knots, scalers, hyperparameters, imputations, stacking) is fit inside each outer-training split.

**Covariate set (primary): P0 = age (restricted cubic spline, 4 knots at train-fold percentiles) + sex.** Age is capped at 80 in
NHANES. Microbiome block M = the v2 genus features (section 1). Arms, for BOTH learners (logistic L2; CatBoost with the same
6-configuration inner-5-fold tuning budget, depth {2,4,6} x iterations {100,200}, tuned on outer-training rows only):

| Arm | Content | Role |
|---|---|---|
| P0 | age spline + sex | reference |
| P0+Z | P0 + detection count + log depth | richness/depth comparator |
| P0+M+Z | P0 + v2 genera + Z | **primary arm** |
| M | v2 genera only | for the within-stratum diagnostic |

**Logistic learner specification (v2; replaces amendment 3 item 2 for Part B; CatBoost unchanged).**

1. **Blocks.** The P0 block is the age restricted cubic spline (4 knots, 3 columns) plus sex (4 columns). The penalized block is M (278 columns: 139 ranks with 0 for absent genera, 139 presence indicators) plus Z (`nd`, depth) in the arms that include them.
2. **Penalty.** P0 columns are protected: after standardization they are multiplied by 1000, so their effective ridge penalty is 10^-6 of the penalty on M and Z (practically unpenalized and numerically stable). M and Z share one penalty with inverse strength C. The P0 arm has no penalized block and is fitted once with C = 1 (all columns protected); the M arm has no P0 block and all its columns are penalized. Inner and outer fits are identical in form.
3. **Grid, fixed in advance.** C in the 13 points 10^-7, 10^-6.5, 10^-6, ..., 10^-1 (half-decade spacing). It is fixed from theory and not tuned on any K2 draw: under a null block the best penalty is infinite, so the floor must make M numerically inert (with about 7,700 standardized training rows, C = 10^-7 gives M coefficients of order 10^-6),
   and the ceiling is where 282 columns on about 660 training cases cost more AUC through estimation noise alone than any realistic increment (a 2p/n rule of thumb). Disclosure: the authors read the K2 outputs and the reviews before fixing this grid, so it is not independent of that exposure; it is validated on fresh synthetic seeds (section 10, Q3) and is not changed after those results.
4. **Selection.** Within the outer-training rows, stratified inner 5-fold CV (seed 42). For each arm with a penalized block, C maximizes the mean inner-fold ROC AUC; ties within 1e-4 go to the smaller C. This matches the endpoint (AUC) and the CatBoost tuning rule (amendment 3 item 4); log loss on balanced-weight probabilities is not used (amendment 3 item 2 is replaced).
5. **Fold-local preprocessing.** Within each inner fold, the spline knots (at the registered train-fold percentiles of the inner-training ages), the standardization means and SDs, and any other fitted preprocessing are computed on the inner-training rows only; the final fit recomputes them on all outer-training rows. Nothing computed on an inner-validation or outer-test row reaches any inner fit.
6. **Class weights.** `class_weight = "balanced"` in every logistic fit (inner and outer, every arm), matching CatBoost `Balanced`. Because the weights make unweighted log loss uninformative, selection uses AUC (item 4).
7. **Logging.** Every fold record stores the selected C, the inner-AUC curve over the grid, the knots and a hash of the scaler means, per arm and learner (CatBoost: depth, iterations, inner AUC).

**Populations (v2).** Primary: all 9,683 rows are fitted and scored (see section 3.6 for the 33 rows with `nd = 0`). Sensitivity S2 (secondary): the same contrast with the 33 `nd = 0` rows removed from fitting and scoring in both arms.

## 7. Primary endpoint and decision rules (carried forward; v2 changes the wording of one band only)

Per learner and seed s, `DeltaAUC_s = AUC(P0+M+Z) - AUC(P0)` on pooled outer-test predictions; estimate = mean over the R seeds (OC1), plus
the across-seed distribution. CI = paired participant bootstrap (2,000 replicates, cases and controls resampled separately,
identical indices for both arms, the seed-averaged DeltaAUC recomputed per replicate); decision additionally needs the seed
guard (>= 80% of seeds with the same sign as the point estimate). Bands (OC1, section S; numbers unchanged): material `lo >= 0.02`; small but real `0 < lo < 0.02`;
no benefit above 0.01 `lo <= 0 and hi < 0.01`; inconclusive `lo <= 0 and hi >= 0.01`; below reference `hi < 0` (v2: named "harm" in the registered plan; renamed, see "Reading a negative contrast" below). Combining learners:
intersection-union (claim "the microbiome adds beyond age and sex" requires `lo > 0` for BOTH learners; one learner only means
"learner-dependent, not established"). Pre-specified decomposition, secondary and unadjusted: `AUC(P0+Z) - AUC(P0)` (richness/depth)
and `AUC(P0+M+Z) - AUC(P0+Z)` (content beyond richness/depth), same bootstrap. Log loss, Brier and calibration slope/intercept are
complementary only. No other endpoint can rescue a failed primary. The fold-matched within-stratum diagnostic (age-year x sex x outer
fold, exact 0.5 for covariate-only scores, within-stratum label permutation null refitting the full pipeline) is carried
forward as secondary, with the permutation count and cost in section 12.

**Reading a negative contrast (v2).** A larger model that must estimate many extra coefficients can lose out-of-sample AUC to a smaller nested model even when the extra columns carry no signal (finite-sample cost). Under within-stratum label permutation both learners showed this in the failed sample (logistic -0.0295, CatBoost -0.0037 mean over 20 draws).
A negative contrast is therefore reported as "below reference: the larger model discriminated worse out of sample" and is NOT called harm and is not evidence that the microbiome is harmful. The bands are not re-centered: a negative null offset can only make a positive call more conservative, and a re-centering would put a data-estimated quantity into the decision.
Every Part B table prints, beside each DeltaAUC, the pipeline's own null offset: the mean DeltaAUC of the within-stratum permutation diagnostic of this section (200 permutations, OC2), with its Monte Carlo interval, as a descriptive companion that is never subtracted. The claim "the microbiome adds beyond age and sex" is unchanged (both learners, `lo > 0`, seed guard).

## 8. Sensitivity S1: BMI, smoking and race/ethnicity, with missingness rules from observed data

S1 = P0 + BMI + smoking + race/ethnicity added as ONE block (never one at a time), for P0 and P0+M+Z, via the downloaded
`BMX_F/G` and `SMQ_F/G` files (provenance `data/external/nhanes_bmx_smq_provenance.json`). Variables: BMI `BMXBMI` (continuous, 3-knot
spline); smoking category from `SMQ020` (ever >= 100 cigarettes) and `SMQ040` (now smoke every day / some days / not at all):
never / former / current; `RIDRETH1` (5 levels as recorded, a social category, not ancestry).

**Observed missingness in the 9,683 study rows (join on SEQN; descriptive only; no outcome-bearing fit):**

| Variable | Missing / no usable value | Why |
|---|---|---|
| BMXBMI | 76 rows (0.78%); 2 rows have no BMX record, 74 present but blank (cases 10, controls 66) | exam non-completion; 12 of the 76 are ages 14-17 |
| SMQ020 | 1,681 rows (17.36%): ALL rows aged 14-19 (1,681 of 1,681), NONE of the 8,002 rows aged >= 20 | structural: asked only of age >= 20 (cases 9, controls 1,672) |
| SMQ020 code 9 ("don't know") | 2 rows | |
| SMQ040 | 6,220 rows (64.24%) | asked only if SMQ020 = 1 (3,463 rows); 0 missing among those asked; 2 coded 7 (refused) |
| RIDRETH1 | 0 rows | |

Rules, fixed now from these counts (not from any outcome):
- **BMI** (0.78% missing, below the 5% bar of the earlier draft): complete-case on BMI for S1 with the P0 and P0+M+Z contrasts repeated on
  the identical rows; the dropped 76 rows are listed by SEQN. The 2:10:66 case/control imbalance of the missing rows is reported.
- **Smoking** is not "missing at random" in children: the S1 primary restricts to age >= 20 (8,002 rows) and the P0 contrast is
  re-run on those same rows. For age >= 20: never = SMQ020 = 2; former = SMQ020 = 1 and SMQ040 = 3; current = SMQ020 = 1 and SMQ040 in {1, 2};
  SMQ020 code 9 and SMQ040 code 7 (4 rows in total) go to a fourth level "unknown" (not imputed, not dropped).
- A second S1 variant keeps all 9,683 rows with smoking = "not asked (age < 20)" as its own level, to show the dependence on the
  age restriction. Both are reported; the age >= 20 version is the S1 headline.
- No outcome-based row selection. The same decision table is used and S1 never replaces the P0 primary.

## 9. Part B outcomes that are NOT claimed

Self-reported diabetes, 2009-2012, unweighted (survey design variables unused), medication and periodontal status not modeled, association
not causation, not clinical utility. The cohort labels in Part A are not NHANES labels and the two parts are never pooled into one claim.

# CONTROLS, COMPUTE, ANCHOR

## 10. Controls, qualification and sample run that must pass before any full run (v2; replaces the registered section 10)

Criteria are written here before anything runs, each with the result that would mean the design is broken. A control that has never been seen to fail is not trusted: every control has a deliberate bad-case twin or an expected-failure leg. The run harness refuses a full run unless a validation record exists whose
input, script, preregistration and control-schema hashes equal the current ones (the K7 binding) and whose output hashes verify (E2). Numerical thresholds below are fixed here before any qualification run; they are provisional until the owner adopts this text, and a threshold is never edited after a qualification run.

**Fresh seeds.** Qualification and the new sample use only fresh seeds and a new output folder. NOT used for any qualification draw: label seeds 1000-1019, 2000, 77, 6, 20261119 (all used or touched by the failed sample or its reviews), nor the primary seeds (fold seeds 1-20, model seed 42, bootstrap seed 20261117). Allocated: label and mechanism seeds 51000-51999
(K2 51000-51039, K3 family 51100-51299, transport cells from 51400 with one seed per draw; the D5 level computation used 7300000-7320999, which qualification must not reuse), fold seeds 101-105, bootstrap seeds 20270101 + draw index. The failed sample's files are never overwritten and never read by a qualification stage.

### Part A controls

| ID | Control | Pass criterion (written first) | Broken if |
|---|---|---|---|
| KA1 | Known good: the old representation reproduces the published numbers exactly (unchanged from the registered plan) | all six source-study LOSO K30 AUCs equal `validation_panel.json` to 1e-9, and the six external full and panel AUCs plus the frozen-panel fingerprint equal the published values to 1e-9 on this machine (0.0005 elsewhere) | any difference |
| KA2 | Richness mechanism, shared (v2; D4). Synthetic labels drawn independently for every participant in BOTH the source training rows and the target, from the same function of the within-study standardized detection count, `logit P(y=1) = c_s + a z_nd`, with `a` set so the oracle expected AUC is 0.75 and `c_s` set per study for prevalence 0.5. 100 draws per direction (up, down); T1/T2/T3 refit on the synthetic source labels each draw; targets: the held-out Shandong table (n = 130) and each external count table (label-free, synthetic labels only) | oracle (the generating score) shows "transfer" in at least 95% of draws; T3 detects in the planted direction in at least 80%; T2 transfers (planted direction) in at least 80% at BOTH K; Monte Carlo Wilson 95% intervals printed | the design cannot recognize a richness signal that the models were taught |
| KA3 | Null twin: labels independent of everything, source and target (200 draws) | T2 false-call rate (transfer or reversal) at most 0.10 at both K; T3 false-call rate at most 0.10; the report prints no "richness-compatible" statement in more than 10% of draws | anti-conservative; or a statement made from noise |
| KA4 | Content mechanism, shared: synthetic labels from the within-detected rank of ONE genus g*, residualized on `nd` and depth within each study (zero if not detected), same coefficient in source and target, oracle expected AUC 0.75, prevalence 0.5 (100 draws). g* is chosen label-free: the genus with the largest minimum detection fraction over the six source studies and the target (ties by name), so it is detected in NHANES | oracle "transfer" in at least 95%; T2 transfers at both K in at least 80%; T3 false-call at most 0.10 | the models cannot recover real content signal they were taught, or T3 absorbs it |
| KA4x | Shifted target: the KA4 mechanism with sign + in the source and sign - in the target (100 draws) | T2 shows "reversal" in at least 80% at both K | reversals cannot be recognized |
| KA4s | Stress tests, REPORT ONLY (no criterion): the registered target-only constructions (labels from detection count for KA2, from one panel genus for KA4) with independently generated participants at native n (no row duplication), 100 draws, Wilson intervals | none; reported with the shared-mechanism cells | not applicable |
| KA5 | Representation unit tests (unchanged) | all hold; each shown RED on the v1 function first | any failure |
| KA6 | Amendment-4 gates still green on v2 (unchanged) | `tests/test_transfer_defects.py` and `check_transfer_protocol.py --require-controls` pass | any failure |
| KA7 | Richness-report cells (v2; D3), pure score simulation with independent participants (88 cases, 264 controls per draw, 200 draws per cell, binormal scores with the stated true AUCs): chance/chance (T2 0.5, T3 0.5); T2 signal/T3 chance (0.75, 0.5); T2 chance/T3 signal (0.5, 0.75); comparable non-chance (0.70, 0.70); T3 informative, T2 worse (0.55, 0.75) | chance/chance: T2 false-call at most 0.10, T3 uninformative in at least 90%; 0.75/0.5: T2 transfers in at least 90% and T3 is uninformative in at least 90%; 0.5/0.75: the table row "inconclusive or reversal with T3 informative" is produced in at least 80%; 0.70/0.70: "comparable" or "not resolved" in at least 90% and "exceeds" or "below" in at most 10%; 0.55/0.75: "T2 below richness" in at least 80% | the report mislabels a known configuration |
| KA8 | Study-identity control (v2; D6): synthetic label equals study (1 for the five clinical source studies, 0 for NHANES), T2 trained on a random 80% of source rows, evaluated on the other 20% | held-out AUC at least 0.95 AND the identity share of mean |SHAP| (section 3.8) at least 0.20 (about five times the uniform share 6/139); twin: labels permuted within study, identity share below 0.20 in at least 9 of 10 permutations | the identity proxy cannot be caught |

### Part B controls

| ID | Control | Pass criterion (written first) | Broken if |
|---|---|---|---|
| K1 | Reproduce the baseline A and B with the original pipeline (unchanged) | A in 0.803 +/- 0.002 and B in 0.698 +/- 0.002 | outside either interval |
| K2 | Label permutation within age x sex strata, full v2 pipeline (section 6), 40 draws, fresh seeds | per learner: mean DeltaAUC within +/- 0.005; at most 3 of 40 CI lower bounds above 0; counts with `hi < 0` printed without a criterion (Monte Carlo Wilson intervals printed) | a signal is detected in permuted data, or the pipeline carries a larger finite-sample cost than 0.005 |
| K3 | Injected feature (v2; D5). Estimand: the REALIZED pooled AUC of the injected feature against the label on the analysis rows (the age/sex-matched AUC is logged beside it and must lie within 0.015 of it). The shift is solved by bisection on the realized draw so the realized pooled AUC equals the target within 0.002 (delivery check BEFORE any fit; a draw that cannot be delivered is a failure). Levels 0.50, 0.60 and 0.64 with 10 distinct seeds each; 0.55 and 0.70 with 5 seeds each (report only, non-gating); a distinct seed for every level and run. The gating level 0.64 is set by the decision rule (owner decision 2026-11-19): it is the injected-feature AUC whose ORACLE incremental DeltaAUC over the age and sex baseline equals the plan's material band of 0.02, computed on synthetic data only (NHANES-sized: 9,683 rows, 830 cases; baseline AUC 0.800; 100 fresh seeds per level on seeds 7300000-7320999, none used elsewhere; no real label; `drafts/d5_material_level/`): the mean oracle gain is 0.0200 at AUC 0.638 (Monte Carlo 95% interval 0.637-0.638; equal-variance binormal closed form 0.641), rounded to 0.64, where the oracle gain is 0.0208 (SD 0.0019 across seeds) | at 0.64 (strong positive, the material-increment level): both learners `lo > 0` in at least 8 of 10 seeds and the median fraction of the ORACLE incremental gain recovered at least 0.5 (oracle gain: AUC of the out-of-fold P0 score plus the exact log likelihood ratio of the feature, minus the P0 AUC, no fit); at 0.50 (null twin): per learner |mean DeltaAUC| at most 0.005 and at most 1 of 10 with `lo > 0`; levels 0.55-0.65 are reported with the oracle gain and the detection rate, and the smallest level detected in at least 8 of 10 seeds is stated as the minimum detectable increment. Limitation stated: the sensitivity gate is tied to the decision rule, so a feature block whose oracle increment is below about 0.02 DeltaAUC is not guaranteed to be detected; the 0.64 gate certifies detection of an increment of the size the plan calls material, not of smaller ones | the pipeline cannot find a strong feature, or finds one in a null |
| K4 | Leakage asserts (v2; E5): outer folds disjoint and an exact partition; no outer-test row or label reaches inner tuning, knots, scalers; the pass expression requires that replacing outer-test covariates changed predictions; PLUS a deliberately leaky twin (knots computed on all rows) that the same assert must flag | all asserts hold and the leaky twin is flagged | any violation, or the twin passes |
| K5 | Covariate-only within-stratum fold-matched AUC (unchanged) | exactly 0.5 (within 1e-12) for logistic and CatBoost; its noisy twin differs | any deviation |
| K6 | Proxy control: simulated label depending only on detection count (KA2 mechanism on NHANES rows, source-only) (v2; E6) | P0+Z beats P0 (lo greater than 0) and the content-beyond-Z contrast has `lo <= 0` AND a point estimate of at least -0.005 (a significantly or materially negative contrast no longer passes) | the proxy is not separated, or the content contrast is materially negative |
| K7 | Provenance binding (unchanged) | equal | any mismatch |

### Qualification plan (v2; synthetic or permuted labels only; no real outcome is scored)

Order, and no stage starts before the previous one passed; the criteria above and below are frozen before Q1 starts.

- **Q0 Engineering gates.** The E1-E8 unit tests pass, each shown red first: stale, partial, duplicate and swapped records are refused; the K2 resume refuses a changed seed, setting or count; the timing verdict can fail; the K6 criterion evaluates FAIL on the retained failed-sample K6 file; the K4 leaky twin is flagged; no stage that is tagged synthetic-label can read a real outcome array (a unit test over the stage code paths).
- **Q1 Reporting rules (KA7).** Pure simulation, minutes.
- **Q2 Shared-mechanism transport (KA2, KA3, KA4, KA4x, KA4s) and the identity control (KA8).** Draw counts above (100, 200 for null cells); false-failure probabilities of the thresholds are printed (for example, a true null false-call rate of 0.05 fails "at most 20 of 200" with probability 0.001, and a true rate of 0.08 fails it with probability 0.12).
- **Q3 Part B under D1 (K2, K3 family).** 40 permutation draws and the K3 family on fresh seeds; fold seeds 101-105 (one per run, cycling); every selected C logged.
- **Q4 Timing and threads.** Threads pinned (D9); the timing verdict compares the median measured per-fit seconds per (learner, arm) with the ceilings of section 12 (twice the planning costs); a timing failure fails qualification.
- **Sample v2.** Only after Q0-Q4 pass: one source study (`china_shandong_sun`, n = 130) held out and run end to end through the v2 pipeline on PERMUTED or SYNTHETIC labels only (source-training labels synthetic from the KA2/KA4 mechanisms or permuted within study; the target's labels permuted within the study), written to a NEW folder `data/processed/reanalysis_sample_v2/`,
  with the Part B pipeline on seed 101 (not 1), one outer fold, fixed untuned configuration, timings logged per stage, and a new record `osf/sample_validation_record_v2.json` (E2). No real Shandong v2 score is produced by this step. Its AUC values are not results.
- **Owner decision.** The owner reads the qualification and sample reports and decides on the full run. This plan does not authorize it.

**Baseline controls v2 (OC3)** are unchanged in purpose: re-run into `data/processed/baseline_age_sex_controls_v2.json` (done once in the failed sample; reused only if its hashes still bind, otherwise re-run).

**Development firewall (v2; replaces the registered wording; D7).** Real labels of the source studies, including NHANES, are used to TRAIN v2 models and to choose their hyperparameters by inner cross-validation, as any transfer design requires; inner losses and AUCs on those rows are internal to tuning and are never reported as results.
No v2 model is SCORED against real labels of any external cohort, of any held-out source study, or of NHANES (reported outer-test or endpoint evaluation) until the owner approves the full run. After the failed sample (which produced real held-out Shandong values, disclosed in section 0A-2) no further real-label sample score of any v2 model is produced; qualification and sample v2 use synthetic or permuted labels only.
Label files may be read only to decide row inclusion (rows with a recorded 0/1 label, as in every v1 analysis); the label-disabled loader does this and returns no labels (disclosed).

**Treatment delivered check.** Each run logs, from the run itself and not from the output shape: the representation tag, the count of NaN cells per cohort (equal to the absent-genus counts of section 4), the model feature list, the fold hash, the thread settings (D9), the realized effect of every injected feature (D5) and the selected hyperparameters of every fit (E1).

## 11. Data added for S1 (done in preparation; public CDC files)

`BMX_F`, `BMX_G`, `SMQ_F`, `SMQ_G` (NHANES 2009-2010, 2011-2012) downloaded 2026-11-17 from `wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{2009|2011}/DataFiles/`,
stored in `data/external/` beside `DIQ_F/G.XPT` (tracked in git, not LFS, same as DIQ), SHA-256/size/URL in
`data/external/nhanes_bmx_smq_provenance.json`, NCHS terms (statistical use only, no re-identification, no linkage to identify) recorded in
the repository `DATA-LICENSE.md`. Read in isolated mode with pandas; nothing executed; nothing fit.

## 12. Compute estimate (v2; replaces the registered section 12 using the sample's measured timings)

**Measured (failed sample, 2026-11-19; `part_b_sample_leg.json`, `k2.json`, `k3.json`; CatBoost `thread_count=4`).** CatBoost per fit: P0 0.25 s (0.10 in K2), P0+Z 0.20 s, P0+M+Z 0.68 s, M 0.68 s. Logistic per fit at the sample's unpinned BLAS threads: P0 0.06 s, P0+Z 0.12 s, P0+M+Z 1.41 s (1.13-1.48 s in K2/K3), M 0.71 s.
The registered timing criterion (measured within 2x of the section 12 planning cost, ceiling 0.60 s for logistic) FAILED for logistic P0+M+Z and M (amendment 8). A bounded check in the Fable review with BLAS capped at 4 threads measured 0.30 s for the same C = 1 P0+M+Z fit (SUGGESTIVE: thread oversubscription; one measurement). Threads are therefore pinned (D9) and the timing verdict becomes part of the validation record.

**Thread pinning and timing verdict (v2; D9).** Before numpy, scikit-learn or CatBoost is imported, the run sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` and `MKL_NUM_THREADS` to 4 and CatBoost `thread_count` to 4; the effective values are read back (for example with `threadpoolctl`) and written to every stage record, and a mismatch stops the stage.
Every validation record carries a timing verdict: for each (learner, arm) the median measured per-fit seconds is compared with the ceiling (twice the planning cost below); `timing_pass` is false if any ceiling is exceeded, and `all_pass` requires `timing_pass`.
**Projection, not measurement.** Logistic per-fit costs at 4 threads: P0+M+Z 0.30 s (the one measured value); M 0.15 s, P0+Z 0.03 s and P0 0.01 s are the sample values scaled by 0.30/1.41 and must be replaced by measured values in sample v2. The planning costs and the ceilings of the timing verdict stay at the registered values (logistic 0.3 s, ceiling 0.6 s; 3-4 feature CatBoost 0.2 s, ceiling 0.4 s; 141-column CatBoost 1.0 s, ceiling 2.0 s),
which the measured 4-thread logistic value and all measured CatBoost values meet.

Fits per (arm, outer fold): CatBoost 6 configurations x 5 inner folds + 1 = 31 (unchanged); logistic 13 grid points x 5 inner folds + 1 = 66 for each arm with a penalized block (P0+Z, P0+M+Z, M) and 1 for P0 (D1).

| Block | Per outer fold (s) | Folds | Est. wall time (serial, `lockf`, 4 threads) |
|---|---|---|---|
| **Qualification (before sample v2; section 10)** | | | |
| K2, 40 permutation draws, arms P0 and P0+M+Z, both learners (about 240 s per draw) | 48 | 200 | **2.7 h** |
| K3 family, 40 runs (about 240 s per run) | 48 | 200 | **2.7 h** |
| Transport cells KA2-KA4x (about 600 draws; CatBoost refits and 10,000-replicate bootstraps on six targets; not measured) | | | **about 2 h** |
| KA7, KA8, Q0 tests | | | **about 0.2 h** |
| Sample v2 | | | **0.1 h** |
| **Full run (only after owner approval)** | | | |
| Part B primary: 4 arms x 2 learners (logistic 33 s + CatBoost 55 s per fold) | 88 | 100 | **2.4 h** |
| S1 (two variants; arms P0 and P0+M+Z) | 48 | 200 | **2.7 h** |
| S2 (33 `nd = 0` rows removed; arms P0 and P0+M+Z) | 48 | 100 | **1.3 h** |
| Within-stratum permutation null, 200 permutations, FIXED configuration (OC2; unchanged) | | | **0.7 h** |
| Part A recomputation, including the identity sensitivities (3.8) | | | **0.6 h** |
| **Total** | | | **qualification about 7.7 h + full run about 7.7 h = about 15 h serial; plan 15-30 h wall on a loaded machine** |

- The qualification is the large new cost (about 7.7 h of a shared machine, one heavy run at a time under `lockf -k /tmp/commandem-swift-build.lock`). Options for the owner: run it at the stated size (recommended: the thresholds in section 10 are computed for these draw counts), or reduce K3 seeds and K2 draws and accept
  wider Monte Carlo intervals (stated in the record). Parallelism beyond four cores is a machine-policy decision, not made here.
- OC2 (the fixed-configuration permutation null) is unchanged. Dropping S1's all-rows variant saves about 1.3 h.
- Memory is not a constraint (128 GB). Staged order: Q0, Q1, Q2, Q3, Q4, sample v2, owner decision, then the full run (Part A first, Part B only if the controls passed).

**The qualification run and the full run each need explicit owner approval** (project sample-validation directive). This text authorizes neither.

## 13. External anchor: OSF Registries registration (chosen by the owner 2026-11-17)

The anchor is a registration on OSF Registries (osf.io/registries) of this exact file, using the OSF "Secondary Data Preregistration" template, with the files named in
`osf/OSF_REGISTRATION_PACKET.md` attached from an OSF project. The owner submits the form; no agent creates an account, project or registration. The repository stays private.
What becomes public: with the OC4 default (no embargo) the registration form, its attached files and a DOI become public when the submission is approved (OSF approves automatically after
48 hours if no administrator acts). With an embargo (alternative), the form and files stay private until the end date and no DOI is issued until then. Nothing else in the repository
becomes public by registering: the attached files are exactly the plan, the manifest and the diagnosis, none of which contains participant-level data. OSF registrations are not editable; changes go
through an OSF Update with a justification or through the deviations policy (section 15). An OpenTimestamps proof of the plan's SHA-256 is an optional independent addition.

## 14. Items needing action before freeze

1. Section S settings OC1-OC4 are owner-confirmed; the prior-knowledge statement (OC5) is final (joint, 2026-11-18). 2. Owner submits the OSF registration; the URL/DOI is recorded as in section 15. 3. After
registration and before any full run: a v2 protocol amendment adopts the representation and re-runs the Amendment-4 gates, since v1 must not score any cohort. 4. (v2) The owner approves the qualification (section 10, about 7.7 h), then, after sample v2 reports, the full run (about 7.7 h; section 12); this plan authorizes neither.

## 15. Reporting, deviations, and the registration record

**Reporting regardless of result.** Every primary (the T2 AUC per external cohort; DeltaAUC per learner in Part B), every secondary and every control is reported with its interval,
whatever the direction and whatever it does to earlier claims: a null, a below-reference result, a failed control, an inconclusive interval and a result that contradicts the diagnosis are published
with the same prominence as a confirmation. A failed control stops the plan (section 10) and the failure is reported, not repaired silently.

**Deviations.** Any change after registration is recorded in a dated, append-only file `PREREGISTRATION_REANALYSIS_AMENDMENTS.md` (trigger, evidence, change, effect, confidence)
before the changed code is used, and in an OSF Update with a justification where OSF allows it. Engineering-only fixes (no estimand, representation, decision rule, seed or band
changes) are labeled ENGINEERING. Anything else is labeled DESIGN CHANGE; a DESIGN CHANGE made after any primary was scored is reported as post hoc and cannot be used to rescue or
replace a primary. The report lists every amendment next to the results it touched (v2: the validation record lists every amendment automatically).

**Historical results.** All v1 numbers stay published as HISTORICAL (section 4), labeled representation-dependent and not interpretable as organism-level evidence, beside the
v2 results. They are not deleted, edited in place or silently replaced.

**Registration record (specification only; the runner is not built here).** After the owner submits the registration, the owner (or an agent given the URL) writes
`osf/registration_record.json`, absent until then:
`{"schema_version": 1, "osf_registration_url": "https://osf.io/<id>/", "osf_registration_doi": "<doi or null if embargoed>", "registered_utc": "<ISO-8601>",
"osf_template": "Secondary Data Preregistration", "embargo_end": "<YYYY-MM-DD or null>", "plan_sha256": "<hash of PREREGISTRATION_REANALYSIS.md as attached>", "manifest_sha256": "<hash of osf/registration_manifest.json as attached>"}`.
The analysis runner (`scripts/run_reanalysis.py`, written after registration) MUST refuse to run, with a REFUSE message and exit status 1, if ANY of the following holds: (R1) `osf/registration_record.json`
is absent or not valid JSON with these fields; (R2) the URL does not match `https://osf.io/[a-z0-9]{5}/`; (R3) `plan_sha256` differs from the current SHA-256 of the plan file or from the manifest's
`candidate_plan.sha256`; (R4) `manifest_sha256` differs from the current manifest file; (R5) `scripts/check_registration_manifest.py` exits nonzero (any drift in a pinned input,
label file, NHANES file, pre-existing script, prior plan or historical result); (R6) the validation record of section 10 for the ADOPTED plan (v2: `osf/sample_validation_record_v2.json`, which lists every amendment, verifies its recorded output hashes, includes the timing verdict in `all_pass`, and is bound to the qualification outputs) is absent, failed, stale, partial, duplicated or bound to different hashes. The runner writes its start time to its
output and refuses if it is earlier than `registered_utc`. Scripts written after registration (section 16) are bound by a separate post-registration hash list committed before the full run;
they are not pinned in the manifest because their behavior is specified by this text.

## 16. Pinned inputs and the scripts to be written after registration

Exact SHA-256 values for every pinned file are in `osf/registration_manifest.json` (attached to the registration; verified by `scripts/check_registration_manifest.py`, which fails on any drift).
Groups: data matrices; label files; NHANES files; protocols and prior plans; historical results; the diagnosis; scripts that exist now. Key pins as of 2026-11-17:

| File | SHA-256 |
|---|---|
| `data/models/processed_data_vsearch.pkl` (audited source matrix) | `21044e93ff394dc3a8339952d5c6d8baede366402f78179344df7ee99150766a` |
| `data/processed/unified_genus_counts.csv` (raw genus counts) | `2aab70a18974d154a085cde9d23c100c8da75b8065b484f9801db5d994149754` |
| `data/processed/nhanes_demographics.csv` | `dd571ed567b3df8a201463c2d9b5a68e46428e319f48f4aaeab93ac335ad3d0e` |
| `data/external/DIQ_F.XPT` | `7e90371cbc98e77a9684eff32ffa0e4ee3e8fc04d97581a8773e19cb9fe901fa` |
| `data/external/DIQ_G.XPT` | `a9d5475e0cd66d6a7bc30230345ed0172a9abcbc0a7a4145a35025c827a52a87` |
| `data/external/BMX_F.XPT` | `1fa42e07764037674c3f56e1e76f990e10c32245897597de3d731c57b91d869a` |
| `data/external/BMX_G.XPT` | `4814bfc3047ed400b9d43d285f8c3ea7c940ac6489404a9b699579715d158ec3` |
| `data/external/SMQ_F.XPT` | `ee85c82ea55046eb7bf491088b5bb9efecbea8aaf66ae8c89123bad23a5f1901` |
| `data/external/SMQ_G.XPT` | `69f2375f036a815082b1e97110e79c505b91e0985c61696f8eaacf94828115dc` |
| NHANES DEMO_F.xpt (not stored; source hash recorded in `nhanes_demographics.provenance.json`) | `78c4d4a6e5eafa9da3bbb24a90d140fef5d8c0cda932a7ff8ee609288d4fae07` |
| NHANES DEMO_G.xpt (not stored; same) | `eaf0525d1952626885af3e935415a1f66ad62c18698080e7354789c125af252d` |

Label files for the external and source cohorts (`data/raw/*/labels.tsv`, `data/external/*.csv`, `data/processed/*_metadata.csv`) are individually pinned in the manifest.

**Scripts written AFTER registration (behavior specified in this text, not pinned by hash). v2 note: if this revision is adopted, the scripts are edited ONLY after adoption (never before), listed again in a new `osf/post_registration_scripts.json` and re-bound; the registered pins in `osf/registration_manifest.json` are never edited:** `scripts/representation_v2.py` (section 1), `scripts/transfer_protocol_v2.py` and
`protocol/transfer_protocol_v2.json` (sections 2 and 14), `scripts/run_reanalysis.py` (the runner; section 15), `scripts/run_reanalysis_controls.py` (KA1-KA6, section 10),
`scripts/reanalysis_part_b.py` (sections 6-8), and `data/processed/baseline_age_sex_controls_v2.json` (OC3). The scripts that exist now are pinned; the v1 code path inside them stays bit-identical (KA1).
