# Reconstruction audit — 2026-10-03

Trigger: dashboard/preprint review found unsupported claims and invalid validation. Implementation was isolated in the Codex workbench. No live deployment or publication is part of this remediation.

| Evidence | Mechanism | Correction | Claim now supportable |
|---|---|---|---|
| PRJNA910326 metadata has 129 DF aliases; original paper deposits oral and fecal specimens | All specimens mislabeled tongue coating locally | Eligibility loader excludes DF and checks unique/matched identities | 10,228 source rows, 1,251 cases; historical vocabulary retained |
| India evaluation shares 50 exact source SRR IDs | Direct fitting/evaluation overlap | Entire Indian source excluded for every current India fit; identity guard rejects residual overlap | Source-study-excluded re-evaluation, not independent accession replication |
| Shanghai paper deposits both PRJNA910326 and PRJNA782768 | Participant independence unresolved | Exclude all 218 Shanghai source rows when fitting, ranking, and calibrating its related benchmark | Exploratory related-study evaluation only |
| PRJNA664107 BioSamples and paper locate Moscow | Incorrect country/specimen provenance | Russia/Moscow, gingival sulcus | No two-Chinese-holdout claim |
| Previous panel artifact ranked only 20 columns and had 49-person results; claimed 50-run output missing | Incomplete feature ranking and unsupported summary | All-column training SHAP, nested source-study K selection, 50 paired seeds | Portugal 30-genus 0.578 vs full 0.646; 29/50 seed wins, mean 0.631 vs 0.616 |
| Observed/null permutation used different fold counts | Different statistics invalidated null comparison | Identical five-fold mean AUC; within-study shuffle preserves composition | Observed 0.794 vs null 0.660; conditional p=1/101, not disease causality |
| Calibration fit and score labels overlapped | Resubstitution optimism | Disjoint fitting/calibration/evaluation rows | Source ECE 0.194→0.006; Portugal 0.319→0.169, still miscalibrated |
| Subgroups used source-trained predictions on source rows | Training-row evaluation | OOF predictions and conditional intervals/error rates | Descriptive NHANES estimates, no fairness certification |
| Oral-only rerun changes primary result | Historical evidence was specimen-contaminated | Withdraw confident reversal and safety remedy | South Africa 0.449 (0.323–0.578), interval includes chance; stable restriction 0.486, mean transfer worsens |
| Ordered-boosting explanation conflicts with fitted CPU parameters | Incorrect mechanism attribution | Verify Plain boosting; withdraw algorithmic story | Fixed historical estimator, not unbiased superiority |
| Clean site build omitted ignored PDF/results; manuscript source could drift | Build depended on preexisting local assets | Canonical tracked PDF/HTML/JSON preparation and hash gates | Clean build includes identical assets; stale inputs fail |
| axe finds low contrast, hidden SVG controls, scroll/landmark defects | Presentation/interaction barriers | Token contrast, keyboard controls, main/H1, focusable tables, HTML paper | Automated checks cover both themes and mobile/desktop; PDF tagging not claimed |
| npm audit reports tooling advisories | Vulnerable transitive tooling chain | Tailwind 4/Vite integration and current Wrangler lockfile | Full and production audit checked locally; no permanent-security claim |

## Protocol and artifacts

scripts/reproduce_audit.py is the fail-fast current entrypoint. requirements-research.txt specifies its Python environment. Current JSON records matrix, eligibility metadata/code, analysis code, parameters, dependencies, and limitations. The dashboard additionally records hashes for the snapshot's source/derived artifacts. Manuscript blocks and figures are generated from these same artifacts; Preprint.build.json ties the canonical PDF/HTML to their source, template, and figures.

The historical input pickle is preserved. Other matrices, model-family comparisons, old notebooks, plots, and older log entries are not revalidated scientific results. Reproducing derived-input claims is not proof of end-to-end raw-read processing. Restricted NHANES reads remain unused.

## Confidence and unresolved issues

Proven by local checks: exact fecal exclusions and sample counts; exact India overlap and whole-study exclusions; row separation in current source/local procedures; regenerated estimates, figures, manuscript assets, and production build. Conditional intervals are specimen-level, not participant-cluster or development-aware uncertainty.

Unresolved: deposited DT184 versus paper oral-case183; participant linkage across related Shanghai studies; repeated-person metadata in other datasets; historical 139-genus vocabulary; heterogeneous raw processing/labels and unmeasured confounding; external adaptive reuse. No new cohort, causal biological mechanism, clinical threshold, decision utility, fairness certification, or validated OOD gate is supplied by this audit. These are explicitly disclosed rather than treated as repaired.

Publication gates: author approval, cohort ethics/reuse dossier, applicable project determination, final privacy/history/LFS review, and explicit owner release approval. Private repository updates do not clear those gates. The dashboard bundles the manuscript, so deploying it during the publication hold is disallowed.

## Verification record

Verified locally: the complete reconstruction runner passed (50 paired seeds, 100 five-fold conditional permutations, all current analyses, and manuscript generation). Eight research unit tests pass in both the existing and a newly installed Python environment. The adaptation demo reproduces the recorded 0/5/10/20/40-label curve. Five asset tests pass, including rejection of stale PDF, results, eligibility code, and source counts. Full and production npm audits report zero advisories. Client/SSR build and asset identity checks pass. Local Cloudflare Pages serves home, RSS, PDF, HTML, and JSON; missing routes return 404. Playwright/axe passes desktop/mobile and dark/light with disclosure panels expanded, keyboard interaction, and no app runtime errors. A tracked-files-only copy passes npm ci/test/build; fresh Python regenerates identical headline metrics, manuscript text, and PNG figures. PDF layout/text was inspected; PDF is untagged, with tested accessible HTML provided instead.

Negative checks recorded: a stale-artifact guard correctly stopped the first concurrent run until the permutation reconstruction finished. The initial browser test used an ambiguous live-region locator; it was corrected. An explicit OS-dark-mode extension then caught two HTML preprint navigation-link contrast failures: transparent browser canvas colors were replaced with explicit paper foreground/background tokens, and the entire viewport/theme suite was rerun. Exact commit/landing and future release gates are recorded in the roadmap.
