# Oral Microbiome Transfer

**Can an oral-microbiome model trained in one collection of studies transfer to another?**
This repository accompanies a retrospective audit of diabetes-status prediction:
checking specimen eligibility, overlapping studies, evaluation procedures and the
conclusions that survive those checks.

**[Explore the research website](https://oralbiome.scarpelli.ai/)** ·
[Read the paper](https://oralbiome.scarpelli.ai/preprint) ·
[Download the PDF](https://oralbiome.scarpelli.ai/preprint.pdf) ·
[Code and reproduction guide](https://oralbiome.scarpelli.ai/code)

> **Release v2026.11.17.2 (2026-11-17).** Pre-DOI review fixes to the paper (no refit, no new analysis). The release v2026.11.17.1 added a preregistered NHANES age-and-sex-only
> baseline (`studies/cross-population-t2d/PREREGISTRATION_AGE_SEX_BASELINE.md`, results in
> `data/processed/baseline_age_sex_v1.json`). Within NHANES, age and sex alone reach
> out-of-fold AUC 0.803 versus 0.698 for the microbiome-only model, and adding the microbiome
> to age and sex shows no evidence of a gain under this learner (depth-4 CatBoost with age and sex appended; 0.802; difference -0.001, -0.009 to 0.007; the interval bounds any gain at about +0.007 AUC), so
> NHANES discrimination is not evidence of microbiome signal beyond demographics. The paper now reports all age and sex strata (Table 6), states that the pooled figure also reflects study-mixture structure, and gives the preregistration provenance. The external
> transfer estimates are unchanged and untested for demographics (those cohorts lack harmonized
> age and sex). **No other number changed.** v2026.11.17.1, v2026.11.17 and v2026.11.15 remain available.

> **Revision 2026-11-17 (release v2026.11.17; second correction).** The paper in
> `studies/cross-population-t2d/docs/Preprint.*` is now the corrected 2026-11-17
> revision, written after an independent re-read: more cautious wording on the
> pooled figure, the South African reversal and age, defined terms, extra rows
> and numbers already held in the retained artifacts, and a manuscript-number
> check (`scripts/check_manuscript_numbers.py`). **No new analysis was run.** It
> supersedes the 2026-10-18 and 2026-11-15 versions. Release v2026.11.15 and its
> asset remain available unchanged. `ARCHIVE_README.md` still calls the paper and
> code "private", which is outdated: the paper, the 59-file code archive and this
> repository are public; only the original research repository and its Git/LFS
> history remain private.

> Exploratory working manuscript; not peer reviewed. All evaluation cohorts
> informed development. This work does not establish a clinical screening tool
> or independently confirmed transfer performance.

## The result at a glance

![Corrected transfer AUCs with conditional 95% bootstrap intervals for Portugal, Mexico, India and South Africa. Hollow circles show separately fitted within-cohort references.](studies/cross-population-t2d/reports/figures/audited_transfer.png)

The four transfer intervals include chance. The within-cohort references are
different fitted models, not clinical ceilings. Uncertainty is conditional on
the observed specimens and fitted scores; it omits unresolved participant
clustering and model-development uncertainty. See the paper for the estimands.

## Start here

| You want to… | Open |
|---|---|
| Understand the study and browse its results | [Research dashboard](https://oralbiome.scarpelli.ai/) |
| Read the methods, findings and limitations | [Paper](https://oralbiome.scarpelli.ai/preprint) |
| Check which finding is supported by which artifact | [Evidence ledger](studies/cross-population-t2d/docs/Audit_Evidence.json) |
| Inspect the numerical analysis | [Analysis scripts](studies/cross-population-t2d/scripts/) |
| Inspect retained statistical outputs | [Aggregate reports](studies/cross-population-t2d/data/processed/) |
| Identify inputs needed for numerical reconstruction | [Input contract](input-contract.json) |
| Verify the repository files | [Repository manifest](MANIFEST.json) |

## What the audit contributes

- **Eligibility:** excludes 129 fecal specimens that had been labeled oral,
  retaining 10,228 source specimens.
- **Study overlap:** excludes the corresponding source studies when evaluating
  overlapping Indian runs and the related Shanghai study.
- **Evaluation:** reconstructs training-only feature selection, consistent
  permutation statistics, disjoint-row calibration and out-of-fold subgroups.
- **Interpretation:** withdraws unsupported confident-reversal and safety-remedy
  claims and keeps the less favorable corrected results.

This is an audit of our own workflow. Several corrections changed together, so
their individual effects on AUC have not been isolated. The contribution is the
documented case and executable checks, rather than a new prediction algorithm.

## Check evidence without participant data

From the repository root, using Python 3:

```sh
cd studies/cross-population-t2d
python3 -S scripts/check_audit_evidence.py
python3 -S scripts/check_manuscript_numbers.py
python3 -S -m unittest discover -s tests -p test_audit_evidence.py -v
```

No downloads or third-party packages are needed for these checks. They verify
file identity, claim completeness and 26 retained aggregate values across nine
findings; the manuscript-number check also confirms that numbers printed in the
paper equal the retained validation artifacts (it re-fits nothing). Deliberately incorrect fixtures exercise rejection behavior. Passing
does not independently reproduce a model result or establish clinical truth.

### Run the synthetic analysis controls

From the study directory above, with Python 3.11:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_release_analysis.py --check-inputs
```

The tests include seven analysis controls, nine evidence-checker controls, seven manuscript-number controls and the age-and-sex baseline unit tests.
They do not train on participant data. The final input check intentionally exits
with status **2** while the 11 omitted historical inputs are missing; that is
the expected safeguard before numerical execution.

## Reproducibility boundary

| Available here | Not supplied or established |
|---|---|
| Reviewed analysis code, pinned Python requirements and synthetic checks | Participant-level matrices, labels and demographic linkages |
| Cohort/fold/seed/genus-level statistical summaries and provenance | Raw reads, reference databases and fitted models |
| Exact hashes and source routes for omitted historical inputs | A procedure proven to rebuild every historical input from those routes |
| Retrospective benchmark results | Untouched confirmatory evaluation or clinical utility |

Numerical reconstruction requires independently obtaining permitted, matching
historical derived inputs. Full raw-to-paper reproduction is not established.
Do not interpret hashes as access to the omitted data. Some unchanged scientific
scripts retain historical motivation in comments; the corrected paper governs
interpretation.

NHANES labels reflect self-reported diabetes rather than verified Type 2 subtype;
clinical cohorts retain heterogeneous deposited labels. Shanghai participant
linkage and its deposited/published case-count discrepancy remain unresolved.
Those limits matter when interpreting transfer.

## Release provenance, citation and licenses

This clean repository snapshot comes from the published November 15, 2026
[reviewed archive](https://oralbiome.scarpelli.ai/downloads/oralbiome-audit-836e92d5b54f.tar.gz).
Its SHA-256 is
`836e92d5b54ff2569344efe0fd191d7d054bbcb130bab41e6af2ca1ad8301248`.
Scientific scripts, reports and tests retain their reviewed bytes except the
files listed under `revision_overlay` in [MANIFEST.json](MANIFEST.json), which
carry the corrected 2026-11-17 paper, the age-and-sex baseline and their checks (releases v2026.11.17, v2026.11.17.1 and v2026.11.17.2). The
archive's original README and manifest are retained as
[ARCHIVE_README.md](ARCHIVE_README.md) and
[ARCHIVE_MANIFEST.json](ARCHIVE_MANIFEST.json); their pre-release labels record
the earlier packaging state. This README and the repository manifest describe
the current layout.

See [CITATION.cff](CITATION.cff) for attribution. The paper is a working manuscript;
no DOI or peer review is claimed. Source code uses the [MIT license](LICENSE).
Original project documentation and statistical outputs use
[CC-BY-4.0](DATA-LICENSE.md), subject to third-party restrictions. Third-party
inputs are not relicensed or redistributed here.

For additional context, figures and the current public release, visit
**[oralbiome.scarpelli.ai](https://oralbiome.scarpelli.ai/)**.
