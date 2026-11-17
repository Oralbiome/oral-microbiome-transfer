# Oral Microbiome Models of Diabetes Status: A Retrospective Audit of Cross-Study Transfer

Jonathan Scarpelli and Ayesha Akhter

Working manuscript, revised 2026-11-17 (fourth revision: pre-DOI review fixes; third revision added the preregistered age-and-sex baseline). Public working manuscript; not peer reviewed.

*Revision 2026-11-17 (fourth revision, 2026-11-17c, after a pre-DOI independent review): wording and reporting corrections to the third revision; no model was refit, no new analysis was run, and every number is read from the retained artifacts. The NHANES discrimination statements now say that the age-and-sex model out-discriminated the microbiome-only model and that the pooled figure also reflects study-mixture structure, which the baseline does not address. The null for adding the microbiome is stated as the preregistered verdict (no evidence of a gain) under this learner (depth-4 CatBoost with age and sex appended), with the interval bounding any gain at about +0.007 AUC and the NHANES-only C falling below A. Section 4.6 now reports every age and sex stratum (Table 6) instead of selected strata, labels the baseline a single preregistered exploratory analysis, and discloses the weak control C4 knot check and the controls file's git_sha. Preregistration provenance is stated in Sections 3.3 and 4.6 (private-repository commit times; the preregistration file is in the public archive). Section 7 gives the file counts of both public archives and Table 1 is kept on one page. Sections revised: Abstract, 2, 3.3, 4.1, 4.6, 6, 7 and the revision notes. This revision supersedes the third-revision text, whose note follows.*

*Revision 2026-11-17 (third revision, 2026-11-17b): a preregistered NHANES age-and-sex-only baseline was added (new Section 4.6; Abstract, Sections 2, 3.3, 4.1, 4.3 to 4.5, 5, 6 and 7 qualified accordingly). In NHANES the age-and-sex model discriminates better than the microbiome-only model and there is no evidence the microbiome adds to it under the tested learner; NHANES discrimination is therefore not presented as microbiome signal beyond demographics, and the external transfer results are unchanged and untested for demographics. No other number changed and no model was refit for this manuscript revision; the baseline values are read from the retained artifacts `data/processed/baseline_age_sex_v1.json` and `baseline_age_sex_controls_v1.json`. This revision supersedes the earlier 2026-11-17 second-correction text, whose notes follow.*

*Revision 2026-11-17 (second correction, after an independent re-read): release-status wording corrected (this paper, the audited code archive and the public release repository are public; only the original research repository and its Git/LFS history remain private); statistic labels, per-study context and definitions of terms added; the interpretation of the pooled figure, the South African reversal and the unavailable adjustment for age made more cautious; additional results already held in the retained artifacts surfaced (Table 2 Russia and related Shanghai rows, calibration in Russia and related Shanghai, panel-selection and seed numbers); and the multiplicity, permutation and selection limits stated. No new analysis was run; previously computed values from the existing artifacts were surfaced. This revision supersedes the 2026-10-18 and 2026-11-15 versions.*

## Abstract

<!-- validation:abstract:start -->
We retrospectively audited oral-microbiome diabetes-status prediction in six source studies, scoring discrimination by the area under the ROC curve (AUC), mostly from out-of-fold (OOF) predictions. Removing 129 fecal specimens mislabeled oral leaves 10,228 source specimens (1,251 cases). Labels from the US National Health and Nutrition Examination Survey (NHANES) encode self-reported diabetes, not a verified subtype; clinical cohorts use deposited diabetes labels. Related India and Shanghai evaluations exclude their entire corresponding source study. Fixed CatBoost yields pooled-source OOF AUC 0.793 (one AUC over pooled out-of-fold predictions; 94.7% of rows are NHANES), but macro-study nested AUC is 0.661 (mean AUC over six held-out source studies, each scored by a model fit on the other five) and held-out NHANES AUC is 0.571. This suggests that the pooled figure largely reflects within-NHANES and study-mixture structure (random folds share studies) rather than transferable signal; the two estimates differ in training set and are not a controlled decomposition. In a preregistered NHANES comparison on the same folds, an age-and-sex-only logistic model reaches OOF AUC 0.803 versus 0.698 for the microbiome-only model, and adding the microbiome to age and sex shows no evidence of a gain under this learner (0.802); NHANES discrimination is therefore not evidence of microbiome signal beyond demographics. This does not test the external transfer estimates, whose cohorts lack harmonized age and sex. Portugal AUC is 0.646 and South Africa AUC 0.449 (conditional 95% interval 0.323–0.578). The South African interval includes chance, so the earlier confident-reversal claim is withdrawn; reversal is neither established nor excluded. Panel size is chosen by source-only nested selection; 30 genera do not consistently improve Portugal (0.578 versus 0.646 for the full fit, but a mean 0.631 versus 0.616 across 50 downsampled seeds with 29/50 wins). A consistent within-study permutation test (observed and permuted statistics computed identically) gives observed mean fold AUC 0.794 (a different statistic from the pooled OOF AUC) versus null 0.660, p=0.0099; because NHANES dominates the rows, this pooled test mostly addresses NHANES and does not adjust for age or sex. Disjoint-row isotonic calibration reduces source ECE (expected calibration error) from 0.194 to 0.006, but external miscalibration remains. Earlier NHANES subgroup AUCs scored training rows; the reported subgroup AUCs use OOF predictions instead. Association directions vary within and between countries without identifying a biological or technical cause. All external cohorts informed development; the cohort-specific transfer AUCs and nested macro AUC are the primary estimands and all other analyses are exploratory with no multiplicity correction. These are not confirmatory estimates. No clinical screening tool, biomarker panel, validated failure gate, or harm-reduction benefit is established.
<!-- validation:abstract:end -->

## 1. Motivation and prior work

The International Diabetes Federation estimates 589 million adults aged 20–79 lived with diabetes in 2024, across all diabetes types, with approximately 252 million undiagnosed [1]. This motivates research but does not establish benefit from microbiome screening. HbA1c does not require fasting, unlike fasting plasma glucose [2]. Saliva collection is noninvasive; shipping and storage depend on the protocol and assay. Sequencing requires laboratory infrastructure and quality control. No cost advantage or clinical decision benefit is established here.

Gao et al. analyzed five salivary studies, including Portugal, and reported pooled random-forest AUC 0.92 and evaluation on an independent Russian subgingival cohort [3]. Yang et al. reported 83.3% accuracy for a four-bacterium classifier in a study incorporating periodontitis [4]. Accuracy and pooled AUC are not directly comparable to our external-study AUCs. Cross-cohort analysis is not novel in itself; this work contributes a reproducible audit of transfer, eligibility, and validation on a heterogeneous survey/clinical mixture. No first European or first cross-continental validation claim is made.

Our question is whether scores and association directions reproduce across studies. Country labels describe cohort provenance, not measured ancestry or an experimentally isolated population effect. Study, specimen, recruitment, periodontitis, treatment, and geography are entangled.

### Audit findings and consequences

| Observed evidence | Correction | Consequence and remaining limit |
|---|---|---|
| 129 deposited DF aliases (the deposit's prefix for fecal specimens; DT and HT mark tongue specimens with diabetes and control labels) were labeled oral in the historical matrix | Exclude fecal rows using deposited aliases | Retain 10,228 oral source rows; historical vocabulary is not newly validated |
| 50 India source identifiers recur in its 60-row benchmark | Exclude the whole Indian source study for India fits | Removes exact-run fitting overlap; benchmark reuse remains |
| Two Shanghai accessions share one publication; the DT (diabetes-labeled tongue) count is 184 versus published 183 | Exclude all 218 Shanghai source rows for related evaluation; disclose discrepancies | Related-study re-evaluation only; participant linkage and count discrepancy unresolved |
| Earlier feature, calibration, permutation and subgroup procedures did not match their claims | Reconstruct training-only selection, disjoint-row calibration, consistent permutations and OOF subgroup scores | Auditable retrospective estimates; no untouched confirmation or clinical validity |

The contribution is a correction of this project’s workflow, not a new prediction
algorithm or an allegation of error in the source publications. The audit changes
what may be concluded: fitting overlap becomes study-excluded re-evaluation,
training-row scores become OOF estimates, self-reported diabetes replaces an
unverified Type 2 target, and earlier confident reversal and safety-remedy claims
are withdrawn. (The withdrawn remedy claims were that restricting the model to stable-sign features, or dropping Atopobium, repaired the South African reversal, and that a distance-based out-of-distribution (OOD) gate could flag unreliable cohorts.) A less favorable result is retained when it is the traceable one.

These are workflow repairs, not causal treatment effects. Historical and current
AUCs differ in eligibility and analysis as well as procedure; subtracting them
would not isolate the benefit of a repair. We have not run a controlled factorial
ablation of the corrections. `docs/Audit_Evidence.json` separates nine findings,
their mechanisms, changes, supported conclusions and remaining limits. It links
retained documentary evidence and unrounded aggregate fields to file hashes;
documentary evidence and aggregate consistency are explicitly distinguished.

## 2. Data eligibility and provenance

<!-- validation:dataset:start -->
Table 1. Cohort identity, specimen, label basis and retained counts.

| Cohort / public accession | Specimen | Label basis (case / control) | N (case / control) | Role |
|---|---|---|---:|---|
| US / NHANES OMP + DIQ_F/G | Oral rinse | DIQ010 yes / no | 9683 (830 / 8853) | Source |
| China / PRJNA910326 | Tongue swab | DT / HT aliases | 218 (184 / 34) | Source; DF excluded |
| China / PRJNA601054 | Saliva | Deposited T2D / control | 130 (103 / 27) | Source |
| China / PRJNA561495 | Saliva | Deposited T2D / control | 102 (70 / 32) | Source |
| India / PRJNA1240053 | Plaque | Deposited T2D / control | 50 (40 / 10) | Source subset |
| China / PRJNA609009 | Saliva | Deposited T2D / control | 45 (24 / 21) | Source |
| Portugal / PRJNA679485 | Saliva | Deposited T2D / control | 50 (25 / 25) | Exploratory benchmark |
| Russia / PRJNA664107 | Gingival sulcus | Deposited diabetes / control | 46 (15 / 31) | Exploratory benchmark |
| China / PRJNA782768 | Oral; subsite unverified | Deposited case / control | 80 (40 / 40) | Related-study; Shanghai source excluded |
| Mexico / PRJNA1208116 | Saliva | Deposited T2D / control | 87 (41 / 46) | Exploratory benchmark |
| India / PRJNA1240053 | Plaque | Deposited T2D / control | 60 (40 / 20) | Source-study-excluded re-evaluation |
| South Africa / PRJNA723337 | Plaque | DM + Known_DM / Normal | 88 (57 / 31) | Exploratory benchmark |
<!-- validation:dataset:end -->

The pipeline identifiers `china_shandong_sun` and `china_anhui_yang` map to PRJNA601054 and PRJNA561495, respectively. Their local region names do not establish recruitment geography; the table uses accessions as study identities. NHANES identifiers refer to the official oral-microbiome project and DIQ_F/G files [13,14], not a new unrestricted SRA deposit. Specimens and deposited case/control definitions vary; the PRJNA782768 oral subsite remains unverified. South African cases combine DM and Known_DM; Pre-DM rows are excluded.

The historical matrix contained 10,357 source rows. PRJNA910326 deposits tongue and fecal specimens [5]; all 347 rows had been labeled tongue coating locally. Deposited DT/HT aliases identify oral specimens and DF aliases fecal specimens. We exclude all 129 DF rows, retain 218 DT/HT rows, and preserve the original matrix as a historical artifact. The paper reports 183 oral diabetic specimens whereas deposited DT aliases yield 184; this single-row discrepancy remains unresolved. We do not guess which row to remove.

India/Mumbai (PRJNA1240053) contains the same 50 SRR identifiers used in the Indian source subset, plus ten controls. Every India evaluation fit excludes the entire 50-row Indian source study. PRJNA782768 and PRJNA910326 were deposited by the same Shanghai publication [5]; different run identifiers do not establish different participants. All 218 Shanghai source rows are excluded from fitting, SHAP (SHapley Additive exPlanations [9]) ranking, and probability calibration when scoring PRJNA782768. This is related-study re-evaluation, not independent replication. PRJNA664107 is from Moscow, Russia, with gingival-sulcus specimens [6], not China. These safeguards cannot undo benchmark reuse or establish participant independence across related publications.

Public SRA-derived counts use the historical VSEARCH closed-reference workflow against the Human Oral Microbiome Database (HOMD) v16.03 [7]. NHANES uses public-use DADA2-derived genus tables; restricted NHANES reads were not accessed. Raw processing is not uniform across all studies. Audited reruns retain the fixed historical 139-genus vocabulary for retrospective comparability, reindex missing genera to zero, and transform each row to average ranks divided by 139. This repairs eligibility, not a newly validated oral-only assay vocabulary. Future confirmation must freeze eligibility, raw processing, and vocabulary derivation independently.

NHANES retained labels correspond exactly to DIQ010: questionnaire code 1 (yes) maps to label 1 for all 830 cases, and code 2 (no) to label 0 for all 8,853 controls; no retained row has borderline, missing or refused/unknown codes [13]. DIQ010 concerns self-reported doctor-diagnosed diabetes and does not establish Type 2 subtype. No additional subtype adjudication rule was verified in the available provenance, so the source-mixture target is diabetes status. A negative self-report is not biochemical confirmation of normoglycaemia. Clinical cohorts retain their deposited labels, with no harmonized subtype/diagnostic adjudication claimed. Recruitment and case prevalence differ greatly. Cross-cohort harmonized adjustment for medication, age, periodontitis, and other confounders is unavailable. Within NHANES, age is available, and the within-age-stratum AUCs (0.576 to 0.608, Table 4) are lower than the within-sex-stratum AUCs (0.689 and 0.707), so a substantial part of NHANES discrimination may reflect age. A preregistered age-and-sex-only baseline (Section 4.6) is consistent with this and goes further: within NHANES, age and sex alone discriminate better than the microbiome-only model (out-of-fold AUC 0.803, 95% CI 0.790–0.816, versus 0.698), and adding the microbiome to age and sex did not improve discrimination under this learner (0.802; difference −0.001, −0.009 to 0.007). NHANES discrimination reported in this paper is therefore not evidence of microbiome signal beyond demographics. The external cohorts have no harmonized age or sex, so this baseline could not be applied to them and whether their transfer AUCs reflect demographics is untested. Labels are self-reported, no survey weights are used, the estimate is conditional on one fold split, and the analysis was preregistered on 2026-11-17. Public sample identities are checked, but specimen-level analyses do not prove unique participants or eliminate repeated-subject dependence. Labels are not standardized incident-disease outcomes.

## 3. Methods and estimands

### 3.1 Fixed retrospective estimators

The primary CatBoost estimator [8] uses 200 iterations, depth 4, learning rate 0.1, balanced class weights, seed 42, four CPU threads, and no training-file writes. Its fitted CPU configuration uses Plain, not Ordered, boosting; the earlier algorithmic explanation is withdrawn. Estimator and parameter choices were developed using older matrices and inspected external results. Historical comparisons do not establish unbiased superiority.

The adaptation probe is balanced logistic regression, C=1. Local fits minimize logistic loss with a quadratic penalty toward source coefficients, lambda=2. Coefficient sign describes a fitted direction in rank space, not a causal bacterial effect. These AUCs are separate from CatBoost's leaderboard; outputs are not calibrated disease risks.

### 3.2 Source and benchmark evaluation

Pooled five-fold stratified OOF AUC (out-of-fold: each specimen is scored by a model that did not see it) estimates discrimination for this source mixture. Nested leave-one-source-study-out (LOSO) uses six outer studies; inner LOSO selects K=30 or 139 by macro-study AUC, retaining 139 on an exact tie. Every reduced fit ranks all 139 columns by mean absolute CatBoost SHAP on at most 1,024 fitting rows. Outer labels do not enter fitting, ranking, or K selection. Model-family and parameter selection remain retrospective.

Three different source-level AUCs appear in this paper and must not be read as one number. (i) The *pooled OOF AUC* is one AUC over all pooled out-of-fold predictions from a single five-fold stratified `cross_val_predict` (reported in the Abstract and Section 4.1; persisted in `data/processed/validation_pooled_oof.json`). (ii) The *mean fold AUC* is the average of the five per-fold AUCs used as the observed statistic of the permutation test (Section 4.3); it differs slightly from (i) because averaging fold AUCs is not the same as pooling predictions. (iii) The *disjoint-row calibration-split AUC* is the raw source OOF AUC on evaluation rows after a separate fit/calibration/evaluation split that trains on a smaller fitting subset (Section 4.4). Their different values reflect different estimators, not different data or contradictory results. Unrounded, the pooled OOF AUC is 0.7934 and the mean fold AUC is 0.7936; the displayed 0.793 versus 0.794 is a rounding artifact of that 0.0002 difference. The macro-study nested AUC is the unweighted mean of the six outer-study AUCs, each from a model fit on the other five studies with panel size selected inside that training set.

Two panel-size summaries also differ by design. The K=30 versus 139 comparison on all six source studies (macro-study AUC 0.684 versus 0.669, "all-source selection") is descriptive: it reports each fixed panel size on every outer study (the SHAP ranking excludes the held-out study) but the choice of K=30 uses all six outer results, so it is optimistic as a selection estimate. The nested macro-study AUC of 0.661 re-selects K inside each outer fold without the held-out study and is the source-level estimate that is free of that selection leak. Neither supports an externally validated panel.

Multiplicity and primary results. No confirmatory hypothesis or analysis plan was fixed before the external cohorts were inspected. The primary reported estimands are the cohort-specific transfer AUCs (Table 2) and the nested macro-study AUC (Table 3). The conditional permutation test, calibration, subgroup and Section 5 investigations, and every pairwise comparison among them are exploratory; p-values and intervals are unadjusted for the number of analyses and should be read as descriptive.

For 50 paired seeds, 500 NHANES rows are sampled without replacement and all other oral-only source rows retained; 30/139-feature fits are scored on Portugal. Seed intervals summarize algorithm/subsample variability on the same 50 specimens, not patient confidence intervals or independent replications.

External cohorts were repeatedly inspected during development. They are exploratory development benchmarks, not untouched validation. India and related Shanghai use source-study-excluded fits. The descriptive three-cohort pooled score concatenates Portugal, Russia, and related Shanghai predictions from different source fits; it is not a single frozen classifier's transfer estimate. Cohort-specific results are primary. Within-cohort CatBoost AUC comes from a separate five-fold OOF fit and is not a clinical ceiling.

AUC intervals use 10,000 stratified case/control bootstrap draws, seed 42, conditional on the fitted score and observed specimens. They omit model/study-selection uncertainty, multiplicity, and unresolved participant clustering. Below-chance AUC indicates reversed ranking, not confidence of individual predictions or demonstrated harm reduction when inversion disappears.

### 3.3 Calibration, permutation, and subgroups

Five outer stratified folds separate fitting, isotonic calibration, and evaluation. Development rows split 75% fitting / 25% calibration; neither uses evaluation labels. External scores average the five fits. Related Shanghai source rows are excluded from fitting and calibration. ECE (expected calibration error: the weighted mean gap between predicted probability and observed case fraction) uses ten equal-width bins, including probability 1; Brier score is also reported. Calibration targets source-mixture prevalence, not destination prevalence.

Observed and permuted statistics use identical five-fold mean-AUC procedures (this is what we call a consistent permutation test). One hundred within-study label shuffles preserve study case counts and composition. The null assumes within-study exchangeability; residual confounding or repeated participants may violate it. This tests conditional association, not causality or transfer.

NHANES subgroup estimates join source OOF predictions to public CDC DEMO_F/G data by SEQN. Two thousand stratified bootstrap draws (versus 10,000 for the cohort-transfer intervals in Section 3.2) give conditional AUC intervals. Sensitivity/specificity use raw threshold 0.5 descriptively. No survey weights, intersectional analysis, clinical threshold, or fairness certification is claimed.

The age-and-sex baseline (Section 4.6) was preregistered before any model was fitted (`PREREGISTRATION_AGE_SEX_BASELINE.md`, commit `bbf833b`, 2026-11-17 13:27; the script and controls commit `0d09c09` followed at 13:36). That commit is in the private research repository, whose history is not public; the preregistration file itself is included in the public archive. It uses the same NHANES rows, self-reported DIQ010 labels, unweighted, and the same pooled five-fold stratified split (seed 42) as the pooled OOF estimate. Model A is unpenalized logistic regression on age (restricted cubic spline, four knots at the 5th, 35th, 65th and 95th percentiles computed on training rows only) and sex, trained on NHANES rows. Model B is the existing microbiome-only CatBoost. Model C is the same CatBoost with age and sex appended (missing for non-NHANES rows, handled natively, which also marks cohort). The primary contrast is AUC(C) minus AUC(A) with a paired stratified bootstrap (2,000 draws, seed 42, percentile 95% interval); the decision rule (interval including 0 means no evidence that the microbiome adds beyond age and sex) and four controls were fixed in advance.

### 3.4 Audit verification and reproducibility boundary

The companion evidence checker uses only the Python standard library and no
participant records. It rejects changed evidence bytes, missing evidence or
aggregate fields, disagreements with recorded numbers, incomplete correction
records, and unsupported isolated-effect claims. Positive and deliberately
incorrect fixtures exercise the same verification function; the extracted
package runs the same checker with third-party imports disabled. These checks
verify retention and consistency, not the truth of original sample metadata or
an independent numerical replication.

Reproducibility has three distinct levels here: the included aggregates and
selected synthetic analysis controls can be checked without participant inputs;
numerical reconstruction requires exact permitted historical derived inputs;
complete raw-read processing and vocabulary derivation remain unverified.
Hashes identify required bytes but do not make omitted matrices obtainable or
redistributable. The released package therefore supports inspection without
claiming an independently reproducible raw-to-paper pipeline.

## 4. Corrected results

### 4.1 Source discrimination and cohort transfer

<!-- validation:transfer:start -->
Pooled-source OOF AUC is 0.793 (pooled out-of-fold predictions, dominated by NHANES; macro-study nested AUC 0.661). Within NHANES, an age-and-sex model (OOF AUC 0.803) discriminates better than the microbiome-only model (0.698; preregistered baseline, Section 4.6), so NHANES discrimination is not evidence of microbiome signal beyond demographics. The pooled figure also reflects study-mixture structure, which this baseline does not address. The descriptive pooled benchmark AUC is 0.594 on 176 specimens, with Shanghai-excluded fitting for its related benchmark. The external cohorts have no harmonized age or sex, so the baseline cannot be applied to them: whether the transfer AUCs below reflect demographics is untested.

Table 2. CatBoost transfer and separately fitted within-cohort OOF references. Intervals are conditional.

| Cohort | N | Transfer AUC (95% interval) | Within-cohort OOF AUC | Source N |
|---|---:|---|---:|---:|
| Portugal | 50 | 0.646 (0.490–0.798) | 0.859 | 10228 |
| Mexico | 87 | 0.611 (0.488–0.727) | 0.566 | 10228 |
| India/Mumbai | 60 | 0.569 (0.410–0.726) | 0.638 | 10178 |
| South Africa | 88 | 0.449 (0.323–0.578) | 0.853 | 10228 |
| Russia/Moscow | 46 | 0.639 (interval not computed) | not computed | 10228 |
| Related Shanghai | 80 | 0.546 (interval not computed) | not computed | 10010 |

Russia/Moscow and related Shanghai come from the retained benchmark artifacts; no bootstrap interval or within-cohort reference was computed for them, and related Shanghai excludes all 218 Shanghai source rows. Within-cohort references are separate fits and not ceilings: in Mexico the within-cohort OOF AUC (0.566) is below its transfer AUC (0.611).

South Africa has a below-chance point estimate (0.449), but its interval includes 0.5, so a confident reversal is not supported. Secondary South African estimates are also below 0.5 (0.486 with the stable-feature restriction, 0.340 without Atopobium, 0.304 for the logistic probe with no local labels, 0.181 for diversity features), but they reuse the same 88 specimens and are not independent confirmations. Reversal is therefore neither established nor excluded. Within-cohort structure remains measurable without proving a transferable disease signal.

![Corrected cohort-specific CatBoost transfer estimates with conditional 95% bootstrap intervals. Hollow circles are separately fitted within-cohort OOF estimates without intervals. The dashed line marks chance. India excludes its overlapping source study. South Africa is not distinguishable from chance by this interval.](reports/figures/audited_transfer.png){ width=90% }
<!-- validation:transfer:end -->

### 4.2 Source-only feature selection and seed sensitivity

Previous claims that 30 genera improved Portugal to 0.683 and that 50 seeds averaged 0.718 with 48 wins lacked matching generated runs and are withdrawn. Historical 49-specimen feature-selection artifacts, older model comparisons, and mixed-specimen results remain research history, not current evidence.

<!-- validation:panel:start -->
Nested source-study selection yields macro LOSO AUC 0.661, which is below fixed K=139 across the same six outer studies (0.669); the all-source (outer-result) comparison, 0.684 versus 0.669, favors K=30 but is optimistic (Section 3.2). The fully ranked 30-genus model scores 0.578 in Portugal versus 0.646 for 139 genera, and 0.624 versus 0.594 on the three-cohort benchmark. Source-study selection does not imply external improvement.

Across 50 paired seeds, NHANES=500 plus all other source studies gives a 30-genus mean Portugal AUC 0.631 (SD 0.048) versus 0.616 (SD 0.057) for all features; the panel wins 29/50. Its seed 2.5th to 97.5th percentiles are 0.547 to 0.722. These are correlated sensitivity runs on the same 50-person benchmark, not a patient confidence interval. No reduced assay or clinical panel is validated. Full rankings, nested fold choices, and paired runs are in `data/processed/validation_panel.json`.

![Reconstructed exploratory results. Left: 30 versus 139 genera on external benchmarks. Center: each point is a paired downsampling seed on the same Portugal cohort; the diagonal marks equal AUC. Right: disjoint source-row calibration improves ECE but substantial external miscalibration remains. These panels are descriptive and do not represent independent cohort replications.](reports/figures/validation_reconstruction.png){ width=100% }
<!-- validation:panel:end -->

<!-- validation:nested:start -->
Table 3. Outer nested source-study results; inner LOSO selects panel size.

| Held source study | N | Inner-selected K | Outer AUC |
|---|---:|---:|---:|
| china_anhui_yang | 102 | 139 | 0.602 |
| china_shandong_sun | 130 | 30 | 0.768 |
| china_shanghai_t2dm | 218 | 30 | 0.738 |
| china_sichuan_liu | 45 | 139 | 0.639 |
| india_maharashtra | 50 | 139 | 0.645 |
| nhanes | 9683 | 30 | 0.571 |
<!-- validation:nested:end -->

### 4.3 Conditional permutation

<!-- validation:permutation:start -->
The reconstructed within-study permutation test on the final matrix gives observed mean fold AUC 0.794 versus a conditional null mean 0.660 (SD 0.008); none of 100 shuffles reaches the observed statistic (corrected p=1/101=0.0099). The null is well above chance because study case counts and study-associated features are preserved. This supports within-study association beyond study composition under the permutation assumptions, but does not establish disease causality or external transfer. It does not adjust for age or sex, so the association it detects within NHANES is not evidence of microbiome signal beyond demographics (see the preregistered age-and-sex baseline below). The observed statistic is the mean of five fold AUCs, not the pooled OOF AUC (0.793) reported in the Abstract. NHANES supplies 94.7% of rows, so this single pooled test (smallest attainable p=1/101) mostly tests within-NHANES association and says little about the clinical cohorts; no per-study permutation was run. See `data/processed/validation_permutation.json`.
<!-- validation:permutation:end -->

### 4.4 Disjoint-row probability calibration

<!-- validation:calibration:start -->
On disjoint outer evaluation rows, source-mixture ECE (10 equal-width bins) changes from 0.194 to 0.006, while Brier score changes from 0.126 to 0.079. Calibration did not improve discrimination (source AUC 0.775 to 0.769). The external ECE changes are Portugal 0.319 to 0.169, Russia/Moscow 0.447 to 0.228, related Shanghai 0.273 to 0.197; on the three-cohort benchmark the ECE changes from 0.317 to 0.176. Source calibration thus improves the fitted source mixture without eliminating external miscalibration; it concerns the probability scale of a mixture dominated by NHANES and is not evidence of microbiome signal beyond age and sex. The raw source AUC on these disjoint evaluation rows is 0.775, a third statistic distinct from the pooled OOF AUC (0.793) and the permutation mean fold AUC (0.794). Full scores, prevalences, and fold metrics are in `data/processed/validation_calibration.json`.
<!-- validation:calibration:end -->

### 4.5 NHANES subgroups

Earlier approximately 0.9 subgroup AUCs evaluated training rows and are withdrawn. These OOF estimates concern NHANES in a pooled-source model, not external demographic groups; they come from the microbiome model without age or sex adjustment and, as Section 4.6 shows, are not evidence of signal beyond demographics. Comparisons are descriptive, not tests of equivalent error rates.

<!-- validation:subgroups:start -->
Table 4. Reconstructed NHANES out-of-fold subgroup discrimination; conditional stratified-bootstrap intervals.

| Group | N (cases) | AUC (95% CI) | Sensitivity / specificity at 0.5 |
|---|---:|---|---|
| sex: Male | 4868 (425) | 0.689 (0.662 to 0.716) | 0.299 / 0.895 |
| sex: Female | 4815 (405) | 0.707 (0.682 to 0.731) | 0.254 / 0.913 |
| age: <40 | 5079 (78) | 0.608 (0.542 to 0.678) | 0.167 / 0.963 |
| age: 40-55 | 2471 (260) | 0.592 (0.557 to 0.627) | 0.192 / 0.882 |
| age: 55-65 | 1523 (329) | 0.576 (0.541 to 0.610) | 0.322 / 0.771 |
| age: 65+ | 610 (163) | 0.597 (0.550 to 0.645) | 0.374 / 0.709 |
| race_ethnicity: White | 3490 (219) | 0.683 (0.647 to 0.721) | 0.265 / 0.899 |
| race_ethnicity: Black | 2340 (265) | 0.697 (0.667 to 0.730) | 0.283 / 0.889 |
| race_ethnicity: Mexican-American | 1688 (159) | 0.734 (0.696 to 0.772) | 0.277 / 0.923 |
| race_ethnicity: Other Hispanic | 984 (100) | 0.668 (0.610 to 0.724) | 0.280 / 0.928 |
| race_ethnicity: Other/Multi | 1181 (87) | 0.712 (0.656 to 0.765) | 0.287 / 0.902 |

The raw threshold is fixed for description, not a clinical recommendation. No survey weighting, subgroup-specific threshold selection, prospective calibration, or fairness certification is claimed. These subgroup AUCs concern the microbiome model alone: within a stratum they are not adjusted for the remaining demographic structure and do not show signal beyond age and sex (see the preregistered baseline in the next section).
<!-- validation:subgroups:end -->

### 4.6 Preregistered NHANES age-and-sex baseline

This section reports a single preregistered exploratory analysis (the preregistration's own label) that answers a question the limitations raised: does the microbiome add discrimination beyond age and sex in NHANES? The design, decision rules and controls were fixed before fitting (Section 3.3). Labels are self-reported DIQ010, unweighted, 9,683 rows (830 cases), one fold split.

Table 5. NHANES out-of-fold AUC for age and sex alone (A), the microbiome alone (B) and both (C). Paired stratified-bootstrap 95% intervals (2,000 draws).

| Model | AUC (95% CI) |
|---|---|
| A: age (spline) + sex | 0.803 (0.790–0.816) |
| B: microbiome only | 0.698 (0.679–0.715) |
| C: microbiome + age + sex | 0.802 (0.788–0.815) |

Contrasts. Adding the microbiome to age and sex changes AUC by −0.0011 (95% CI −0.0093 to 0.0072; C minus A). The interval includes 0, so the preregistered verdict is "no evidence microbiome adds beyond age+sex". This holds under this learner only (depth-4 CatBoost with age and sex appended): the 95% interval bounds any gain at about +0.007 AUC. The microbiome-only model discriminates worse than age and sex alone (B minus A −0.105, −0.124 to −0.087); the preregistered reading was "no better than", and the interval supports the stronger "worse". In the NHANES-only sensitivity analysis (secondary, not decision-bearing), the model trained on NHANES rows with age and sex reaches 0.794 and its difference from A is −0.0085 (−0.0172 to 0.0005). Because this C falls below A, the result is consistent with the learner under-using age, so the null bounds the gain only for this learner and does not show that no other model could extract more. All four preregistered controls passed: the pipeline reproduced the published microbiome-only AUC exactly (0.69776); label-permuted models scored near chance (mean 0.492 for A and 0.491 for C, inside the preregistered 0.47–0.53 range); a synthetic feature with marginal AUC 0.747 added to A was detected (difference 0.052 to 0.070); and the folds were a disjoint partition with spline knots computed on training rows only. Control C4's knot check recomputes the same function on the same training rows and is therefore only a weak guard; the fold-disjointness assertion is the substantive check. The controls file records git_sha `bbf833b` (the preregistration commit) because the controls script ran before its own commit (`0d09c09`).

Exploratory strata. Table 6 reports all four age strata and both sex strata, not a selection. In the 55–65 and 65+ strata the microbiome-only model ranks above age and sex (0.576 versus 0.549; 0.597 versus 0.476), whereas in the under-40 stratum it ranks below (0.608 versus 0.683); in the 40–55 stratum the two are about equal (0.592 versus 0.594) and in both sex strata age and sex rank higher. Adding the microbiome to age and sex (C) is higher than A within the 40–55, 55–65 and 65+ age strata and lower within the under-40 stratum, although the pooled difference is null. Within a stratum the age model has only a narrow age range to use; its below-0.5 AUC in the 65+ stratum (0.476) was not investigated. These stratum comparisons are small, uncorrected for multiplicity, exploratory, and were not part of the preregistered decision; they do not establish that the microbiome carries age-independent signal in older adults.

Table 6. Exploratory NHANES out-of-fold AUC by stratum for age and sex alone (A), the microbiome alone (B) and both (C). One fold split, no intervals, uncorrected for multiplicity.

| Stratum | A: age + sex | B: microbiome only | C: both |
|---|---:|---:|---:|
| Age <40 (n 5079; 78 cases) | 0.683 | 0.608 | 0.654 |
| Age 40–55 (n 2471; 260 cases) | 0.594 | 0.592 | 0.623 |
| Age 55–65 (n 1523; 329 cases) | 0.549 | 0.576 | 0.591 |
| Age 65+ (n 610; 163 cases) | 0.476 | 0.597 | 0.543 |
| Male (n 4868; 425 cases) | 0.799 | 0.689 | 0.797 |
| Female (n 4815; 405 cases) | 0.807 | 0.707 | 0.807 |

Scope. This result concerns within-NHANES discrimination. It does not test the external transfer results (for example Portugal 0.646), because the external cohorts lack harmonized age and sex; whether those transfer AUCs reflect demographics is untested. Values are stored in `data/processed/baseline_age_sex_v1.json` and `data/processed/baseline_age_sex_controls_v1.json`.

## 5. Exploratory transfer investigations

These investigations reuse the benchmarks. They are retrospective modeling tests, not causal identification. Marker associations that include NHANES are not adjusted for age or sex and, given Section 4.6, may partly reflect demographics.

<!-- validation:experiments:start -->
Marker directions use the per-genus point-biserial correlation r between rank abundance and the diabetes label within each group. A genus is informative in a group when |r| is at least 0.15; a flipper has r of at least +0.15 in one group and at most -0.15 in another; the stable-sign rule requires consistent sign among voting groups (thresholds are given after this section).

68% of 88 genera that are informative in at least two geographic groups excluding NHANES reverse sign; separately, across all 139 genera and six groups including NHANES, 14 meet the retrospective stable-sign rule and 58 meet the broader flipper rule. These counts use different group sets and denominators; they are not parts of one partition of the 88 genera, and the retained artifact does not record their overlap.

Portability restriction: mean four-cohort AUC changes from 0.569 to 0.556. South Africa changes from 0.449 to 0.486, remaining below chance as a point estimate. Dropping Atopobium changes it to 0.340; the previous beneficial-ablation interpretation is withdrawn. These South African estimates reuse the same 88 specimens and are not independent.

Local adaptation: South Africa's logistic probe changes from 0.304 with no local labels to 0.615 at 40 labels; its within-cohort logistic reference is 0.859. These point estimates do not establish clinical calibration or an optimal label requirement.

Distribution diagnostics: domain AUC spans 0.991 to 1.000. Mahalanobis distances are Portugal 9.49, India/Mumbai 10.25, Mexico 10.76, South Africa 21.59. The largest distance is not proof of a calibrated failure detector.

Marker properties: median source-only prevalence is 19.8% for stable genera versus 2.1% for flippers (Mann–Whitney p=0.1881). This underpowered association does not qualify a panel.

Diversity: mean transfer AUC is 0.400 versus 0.569 for taxa; 3/4 diversity point estimates are below chance.

Study/geography comparison: within-China sign reversals 58% of 114 informative genera versus cross-geography 67% of 87 (this comparison uses six groups including NHANES, hence 87 rather than 88 informative genera). Association-vector correlations average 0.170 and -0.026, respectively. This nested comparison does not estimate a causal variance decomposition.
<!-- validation:experiments:end -->

Marker stability uses point-biserial correlations of ranks with deposited labels. The cross-group reversal fraction excludes NHANES and requires absolute correlation at least 0.15 in at least two of five remaining geographic groups. In the marker-stability analysis, a stable feature requires at least five of the six groups to cast a vote (absolute correlation at least 0.05) and 80% sign agreement among the votes. In the leave-one-cohort-out portability restriction, the target cohort is excluded from selection, so the rule is applied to the five remaining groups with a lower floor (`min_votes` = 4 in the code: at least four of those five voting) and the same 80% agreement; the two rules are therefore not identical and give different stable sets. These retrospective thresholds are not clinical qualification. The association-ranked top-20 list is not SHAP/model importance, excludes Atopobium, and does not monotonically predict transfer.

Portability restriction chooses stable features from groups other than the target before source fitting. Other inspected benchmark labels inform selection: this differs from source-only nested panel selection. Atopobium deletion is model ablation, not microbial intervention. Movement toward chance does not prove safer decisions or useful discrimination.

Adaptation repeats five-fold local splits across 12 seeds, sampling K=0,5,10,20,40 fitting labels only from local development rows. Evaluation rows are disjoint; folds/seeds are correlated. Forty labels consume nearly half the 88-specimen South African cohort. Logistic within-cohort fits are references, not ceilings.

Label-free diagnostics use a balanced domain classifier and regularized Mahalanobis centroid distance in rank space. A retrospective outlier does not establish a refusal threshold or validated failure gate. Four cohorts cannot calibrate such a rule. Distances are model diagnostics, not population distances.

Diversity comprises Shannon, Simpson, and richness within 139 genera, not the full microbiome. Diversity/taxon comparisons differ in fitting family and representation and do not isolate coarse-graining causally. Marker-property comparisons are underpowered; nonsignificance is not equivalence. Within-China/cross-geography reversal comparisons are nested, use different informative denominators, and confound specimens, recruitment, periodontitis, treatment, processing, and sampling noise. They do not partition variance or show study effects dominate biology.

## 6. Interpretation and limitations

Source discrimination on heterogeneous diabetes labels is not evidence of a portable Type 2 diabetes assay. The preregistered baseline (Section 4.6) adds that NHANES discrimination is also not evidence of microbiome signal beyond demographics: age and sex alone reach a higher out-of-fold AUC (0.803) than the microbiome (0.698), and adding the microbiome to them shows no evidence of a gain (difference −0.001, −0.009 to 0.007), under this learner: depth-4 CatBoost with age and sex appended, whose 95% interval bounds any gain at about +0.007 AUC; the NHANES-only C (0.794) falls below A, consistent with the learner under-using age, so the null bounds the gain only for this learner. The pooled AUC, the within-study permutation test, the calibration results and the NHANES subgroup AUCs all rest mostly on NHANES and are not adjusted for age or sex, so they should be read as consistent with, not evidence against, a demographic explanation within NHANES; the pooled AUC additionally reflects study-mixture structure. This does not bear on the external transfer estimates, which have no harmonized age or sex; whether they reflect demographics is untested, and a below-chance or above-chance external AUC remains uninterpreted with respect to age. The elevated conditional permutation null shows study composition can itself support substantial AUC. Because NHANES supplies 94.7% of rows, the single pooled permutation test (smallest attainable p=1/101) mostly tests within-NHANES association; it says little about the clinical cohorts, and no per-study permutation was run. Local fits and inconsistent directions illustrate instability, not a unique explanation. For South Africa, the primary interval includes chance and the secondary below-chance estimates reuse the same 88 specimens, so reversal is neither established nor excluded.

NHANES supplies 94.7% of eligible source rows, with 830/9,683 cases (8.6%),
whereas the other source studies together contribute 421/545 cases (77.2%).
These arithmetic summaries use retained cohort counts, not new fits. Pooled
source discrimination therefore concerns a strongly imbalanced study mixture;
it is not interchangeable with macro-study performance or the discrimination
within NHANES. The conditional null preserves those study case counts. Its
elevated AUC is evidence against interpreting pooled AUC above chance alone as
a transferable diabetes signal. It does not identify which technical or clinical
study differences explain the observed associations.

The audit corrected mixed specimens, related-study evaluation, country provenance, incomplete feature ranking, inconsistent permutation statistics, training-row subgroup evaluation, and overlapping calibration/evaluation labels. These repairs improve traceability but do not create untouched test sets. Residual limits include imperfect labels, unresolved participant linkage and DT count discrepancy, historical vocabulary, heterogeneous specimens/processing, unmeasured confounding, small studies, and adaptive reuse. Raw-read reprocessing of every source and unbiased reruns of every historical model family were not performed.

Clinical use is out of scope. No validated threshold, destination-risk calibration, prospective utility, screening interval, cost, number-needed-to-screen, or qualified qPCR panel is established. Missed cases could delay follow-up; false positives could cause anxiety, unnecessary tests, cost, and unequal access burdens. Research scores must not replace established diagnosis or care.

Future work should add age-and-sex-adjusted evaluation in external cohorts, which requires cohorts with harmonized age and sex, and the frozen transfer protocol (`PREREGISTRATION_TRANSFER_PROTOCOL.md`) should consider demographics when it is applied; this paper notes the point and does not change that protocol. Confirmation requires a frozen eligibility/vocabulary/estimator/calibration/threshold protocol before receiving a new cohort, participant-level separation, multiple harmonized studies per population, and local decision analysis. These are research requirements, not completed actions.

## 7. Ethics, availability, and contributions

This independent secondary analysis uses public-use survey tables and publicly deposited sequence-derived counts, without new participant contact, specimen collection, restricted NHANES access, or re-identification. Public availability alone is not a universal exemption. Applicable review and original consent/reuse terms must be assessed; a formal determination is required only where the relevant rules apply [10]. No new institutional review requirement has been established for the described activity, and no formal exemption or not-human-subject determination is claimed. Source publications report original ethics review and, where accessible, consent. For the Sichuan source study, the publisher's indexed text reports ethics approval and public sequence deposition, but the original consent wording could not be verified through accessible legitimate routes. This documentary gap remains disclosed and unresolved.

The public dashboard accompanies this manuscript with our aggregate statistical summaries. The audited analysis-code archive (59 files at the 2026-11-15 release; 71 files in release v2026.11.17.2, which adds the revised paper, the age-and-sex baseline files and their checks) and a separate clean public release repository (<https://github.com/Oralbiome/oral-microbiome-transfer>) were first published on 2026-11-15; the original research repository and its Git/LFS history remain private. The public releases exclude sample-level matrices, labels, demographic linkages, raw reads, reference databases, fitted models, and repository history. NCHS public-use terms restrict use to statistical analysis/reporting and prohibit identification attempts or linkage to individually identifiable data [11]. NCBI places no restrictions of its own on molecular-data use or distribution but cannot grant third-party rights [12]. These policies support the described statistical-use route; they do not certify original consent scope or provide blanket derivative-data redistribution permission. Source-specific and exact-artifact review is documented in a cohort ethics and reuse dossier that is not publicly available; no project-wide release clearance is claimed.

Contributions: Jonathan Scarpelli, study design, baseline/CatBoost analyses, interpretation, transfer investigations, and manuscript; Ayesha Akhter, preprocessing, exploratory analysis, feature engineering, and gradient-boosting comparison. Both contributed to methods and experiments.

The manuscript is available at <https://oralbiome.scarpelli.ai/preprint.html> (HTML), <https://oralbiome.scarpelli.ai/preprint.pdf> (PDF), and <https://oralbiome.scarpelli.ai/results.json> (aggregate results); this 2026-11-17 fourth revision supersedes the 2026-10-18 and 2026-11-15 versions and the earlier 2026-11-17 second-correction and third-revision texts. The audited code archive and the public release repository were published on 2026-11-15 and are public; release v2026.11.17.2 of that repository contains this revision (v2026.11.17.1 contains the third-revision text and v2026.11.17 the second-correction text). The original research repository and its Git/LFS history remain private. Sample-level derived inputs, labels, demographic linkages, raw reads, reference databases, fitted models and repository history are excluded. Numerical reconstruction requires the exact permitted historical inputs identified by hashes; full raw-to-paper reproduction is not established. Reproduction instructions distinguish the audited entrypoints from historical scripts. No DOI or peer review is claimed.

## References

[1] International Diabetes Federation. “Over 250 million people worldwide unaware they have diabetes, according to new IDF research.” 2025-04-07; release of IDF Diabetes Atlas, 11th edition (2024 estimates). <https://idf.org/news-and-resources/news/idf-diabetes-atlas-11th-edition/>.

[2] NIDDK. “The A1C Test & Diabetes.” <https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test>.

[3] Gao, C., Guo, Y. & Chen, F. “Cross-Cohort Microbiome Analysis of Salivary Biomarkers in Patients With Type 2 Diabetes Mellitus.” Front. Cell. Infect. Microbiol. 12 (2022): 816526. <https://doi.org/10.3389/fcimb.2022.816526>.

[4] Yang, Y. et al. “Changes of saliva microbiota in the onset and after the treatment of diabetes in patients with periodontitis.” Aging 12.13 (2020): 13090–13114. <https://doi.org/10.18632/aging.103399>.

[5] Guo, X.J. et al. “Distribution characteristics of oral microbiota and its relationship with intestinal microbiota in patients with type 2 diabetes mellitus.” Front. Endocrinol. 14 (2023): 1119201. <https://doi.org/10.3389/fendo.2023.1119201>.

[6] “Drift of Subgingival Periodontal Microbiome during Chronic Periodontitis in Type 2 Diabetes Mellitus Patients.” Pathogens 10.5 (2021): 504. <https://doi.org/10.3390/pathogens10050504>.

[7] Rognes, T. et al. “VSEARCH: a versatile open source tool for metagenomics.” PeerJ 4 (2016): e2584.

[8] Prokhorenkova, L. et al. “CatBoost: unbiased boosting with categorical features.” NeurIPS 31 (2018): 6638–6648.

[9] Lundberg, S.M. & Lee, S.I. “A unified approach to interpreting model predictions.” NeurIPS 30 (2017): 4765–4774.

[10] HHS Office for Human Research Protections. “Coded Private Information or Biospecimens Used in Research, Guidance” (2018). <https://www.hhs.gov/ohrp/coded-private-information-or-biospecimens-used-research.html>.

[11] CDC National Center for Health Statistics. “Data User Agreement.” <https://www.cdc.gov/nchs/policy/data-user-agreement.html>. Accessed 2026-10-18.

[12] NCBI. “Policies and Disclaimers,” Molecular Data Usage. <https://www.ncbi.nlm.nih.gov/home/about/policies/>. Accessed 2026-10-18.

[13] CDC/NCHS. NHANES Diabetes Questionnaire, DIQ_F (2009–2010) and DIQ_G (2011–2012), DIQ010. <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2009/DataFiles/DIQ_F.htm>; <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/DIQ_G.htm>.

[14] CDC/NCHS. NHANES 2009–2012 Oral Microbiome: data documentation and public-use files. <https://wwwn.cdc.gov/Nchs/Nhanes/omp/>.
