# Oralbiome retrospective audit: private release candidate

This package contains the current manuscript, code used by the audited numerical
reconstruction, pinned runtime dependencies, synthetic checks and aggregate results.
This analysis-code archive is prepared for private review; its publication and redistribution are not authorized. The dashboard and working manuscript have separate owner authorization for public deployment.
The package manifest records its exact files, hashes and unresolved review items.

## What the paper establishes

This is exploratory retrospective diabetes-status research using 10,228 eligible source
specimens after excluding 129 fecal rows. NHANES labels are self-reported
diabetes rather than verified T2D subtype; clinical cohort labels are deposited
groups. Negative NHANES self-report does not establish normoglycaemia. Related India/Shanghai evaluations
exclude their corresponding source study. All evaluation cohorts informed
development. Portugal AUC is 0.646; South Africa AUC is 0.449 with an interval
including chance. No clinical assay, portable biomarker panel, validated failure
detector or harm-reduction benefit is established.

Some unchanged analysis scripts retain historical motivation in comments and
docstrings. Those historical premises are superseded by the corrected manuscript
and aggregate results. They are preserved to keep the code bytes identical to
the audited run. The scoped editorial review preserves those historical code bytes.

## Check the code without participant data

For the evidence ledger alone, no installation or participant inputs are needed:

```sh
cd studies/cross-population-t2d
python3 -S scripts/check_audit_evidence.py
python3 -S -m unittest discover -s tests -p test_audit_evidence.py -v
```

`docs/Audit_Evidence.json` links nine workflow findings to documentary evidence,
original analysis code and unrounded aggregate values. The checker verifies file
identity, claim completeness and numeric agreement. Wrong-number, changed-byte,
missing-field/evidence and unsupported-effect controls must fail. The retained
October phenotype receipt is included as `docs/Phenotype_Provenance.json`; it is
not a fresh acquisition or verification of clinical diagnosis. The dated
`docs/Audit_Remediation.md` is a historical October record: its release holds and
test/dependency counts describe that run, not the present release state.

The November manuscript revision is private and has not replaced the public
October version. No correction's individual AUC effect was isolated. Consistency
checks do not independently replicate numerical findings or establish source
truth, original consent, participant independence or a new clinical result.

Use Python 3.11. From the extracted package:

```sh
cd studies/cross-population-t2d
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_release_analysis.py --check-inputs
```

The seven analysis controls use synthetic fixtures and mocked estimator fits,
with no data downloads or model training. The added identity control sends real
on-disk count/label fixtures through the original reader: whole-study exclusion
passes, and a deliberately broken source mask triggers the overlap rejection. The input check intentionally exits 2 while required research inputs
are absent. It lists missing or changed files before any fitting or download.

## Numerical reconstruction requires additional inputs

`input-contract.json` lists the exact derived inputs and their hashes, public
source routes and outstanding access/reconstruction limitations. Sample-level
matrices, labels, demographic linkages, raw reads and fitted models are excluded.
Public source availability does not reconstruct the historical feature matrix.
An exact end-to-end raw-read rebuild has not been demonstrated.

After independently obtaining permitted, matching inputs at the listed relative
paths, run the check again, then deliberately start the numerical reconstruction:

```sh
.venv/bin/python scripts/run_release_analysis.py --run
```

This runs the fixed current analyses, including 50 paired seeds and 100
conditional permutations. It can take substantial compute. No full numerical
reconstruction was launched merely to prepare this package.

Install optional rendering tools separately; the lock covers Python runtime
dependencies, not Pandoc, TeX, OS libraries, or platform wheel availability.
A fresh Python 3.11 installation and the six data-free controls are checked on
the recorded macOS host; other operating systems remain unverified.

The original `reproduce_audit.py`, `build_site_data.py` and renderers are included
for provenance. The package runner uses a small documented presentation context
in place of private roadmap/blog history. That context changes presentation
metadata, not estimator, eligibility, feature selection or evaluation logic.
It creates required local output directories and invokes the original scripts.
It does not deploy a website. PDF/HTML regeneration is optional via
`--run --render-paper` and additionally requires Pandoc and XeLaTeX.

## Aggregate results and provenance

The study's `data/processed/` directory contains only the explicitly selected
cohort/fold/seed/genus-level summaries. `headline-results.json` contains the
reported source and cohort metrics. These are retained results, not a new run.
The file manifest pins source scripts, dependencies, paper files and aggregates.
Input hashes identify omitted artifacts; they are not substitutes for those data.

## License and release status

`LICENSE` retains the existing source-code MIT notice verbatim. `DATA-LICENSE.md`
states the project's documentation/data terms subject to source restrictions.
The owner expressly permitted the existing full-name attribution for this
release; the original copyright notice and MIT terms are retained verbatim.
This narrow exception does not permit publishing personal contact details. Third-party raw data/reference
databases are not included. The included `RELEASE-REVIEW.md` records the completed scoped review and
the disclosed Sichuan source-document uncertainty and separate exact-byte/destination approval still required for this code archive. No claim of peer review or clinical validation is made.
