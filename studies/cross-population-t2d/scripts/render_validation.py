#!/usr/bin/env python3
"""Render manuscript result blocks and figures from audited JSON, with stale checks."""
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reconstruct_validation import ROOT, DATA
from audited_data import provenance as eligibility_provenance, load_data


def read(name):
    d = json.loads((ROOT / f"data/processed/validation_{name}.json").read_text())
    if d.get('eligibility') != eligibility_provenance():
        raise ValueError(f"Stale {name} oral eligibility contract")
    if name == 'subgroups' and d['estimator_script_sha256'] != hashlib.sha256((ROOT / 'scripts/reconstruct_validation.py').read_bytes()).hexdigest():
        raise ValueError('Stale subgroup estimator')
    code = ROOT / f"scripts/{'reconstruct_subgroups' if name == 'subgroups' else 'reconstruct_validation'}.py"
    for actual, recorded, label in [
        (hashlib.sha256(DATA.read_bytes()).hexdigest(), d["input_sha256"], "input"),
        (hashlib.sha256(code.read_bytes()).hexdigest(), d["script_sha256"], "script"),
    ]:
        if actual != recorded:
            raise ValueError(f"Stale {name} {label}: regenerate the analysis before rendering")
    return d


def main():
    panel, cal, perm, sub = [read(name) for name in ("panel", "calibration", "permutation", "subgroups")]
    ext = panel["external_benchmarks"]
    down = panel["downsample_reconstruction"]
    f = lambda x: f"{x:.3f}"
    blocks = {
        "permutation": (
            f"The reconstructed within-study permutation test on the final matrix gives observed mean fold AUC {f(perm['observed_auc'])} "
            f"versus a conditional null mean {f(perm['null_mean'])} (SD {f(perm['null_sd'])}); "
            f"none of {perm['n_permutations']} shuffles reaches the observed statistic (corrected p=1/{perm['n_permutations']+1}={perm['p_value']:.4f}). "
            "The null is well above chance because study case counts and study-associated features are preserved. "
            "This supports within-study association beyond study composition under the permutation assumptions, "
            "but does not establish disease causality or external transfer. See `data/processed/validation_permutation.json`."
        ),
        "calibration": (
            f"On disjoint outer evaluation rows, source-mixture ECE (10 equal-width bins) changes from {f(cal['source_oof']['raw']['ece10'])} "
            f"to {f(cal['source_oof']['calibrated']['ece10'])}, while Brier score changes from {f(cal['source_oof']['raw']['brier'])} "
            f"to {f(cal['source_oof']['calibrated']['brier'])}. In Portugal the ensemble's ECE changes from "
            f"{f(cal['external_benchmarks']['holdout']['raw']['ece10'])} to {f(cal['external_benchmarks']['holdout']['calibrated']['ece10'])}; "
            f"on the three-cohort benchmark it changes from {f(cal['external_benchmarks']['holdout_all']['raw']['ece10'])} "
            f"to {f(cal['external_benchmarks']['holdout_all']['calibrated']['ece10'])}. Source calibration thus improves "
            "the fitted source mixture without eliminating external miscalibration. Full scores, prevalences, and fold metrics "
            "are in `data/processed/validation_calibration.json`."
        ),
        "panel": (
            f"Nested source-study selection yields macro LOSO AUC {f(panel['nested_loso']['macro_auc'])}; "
            f"the all-source inner comparison selects K={panel['source_selection']['selected_k']}. "
            f"The fully ranked 30-genus model scores {f(ext['Portugal']['panel30_auc'])} in Portugal versus "
            f"{f(ext['Portugal']['full_auc'])} for 139 genera, and {f(ext['three_cohort_pooled']['panel30_auc'])} "
            f"versus {f(ext['three_cohort_pooled']['full_auc'])} on the three-cohort benchmark. Source-study selection "
            "does not imply external improvement.\n\n"
            f"Across {down['n_seeds']} paired seeds, NHANES=500 plus all other source studies gives a 30-genus mean "
            f"Portugal AUC {f(down['panel30']['mean'])} (SD {f(down['panel30']['sd'])}) versus "
            f"{f(down['full']['mean'])} (SD {f(down['full']['sd'])}) for all features; the panel wins "
            f"{down['panel_wins']}/{down['n_seeds']}. Its seed 2.5th to 97.5th percentiles are "
            f"{f(down['panel30']['seed_percentiles_2_5_97_5'][0])} to {f(down['panel30']['seed_percentiles_2_5_97_5'][1])}. "
            "These are correlated sensitivity runs on the same 50-person benchmark, not a patient confidence interval. "
            "No reduced assay or clinical panel is validated. Full rankings, nested fold choices, and paired runs are "
            "in `data/processed/validation_panel.json`.\n\n"
            "![Reconstructed exploratory results. Left: 30 versus 139 genera on external benchmarks. "
            "Center: each point is a paired downsampling seed on the same Portugal cohort; the diagonal marks equal AUC. "
            "Right: disjoint source-row calibration improves ECE but substantial external miscalibration remains. "
            "These panels are descriptive and do not represent independent cohort replications.](reports/figures/validation_reconstruction.png){ width=100% }"
        ),
    }
    lines = ["Table 4. Reconstructed NHANES out-of-fold subgroup discrimination; conditional stratified-bootstrap intervals.",
             "", "| Group | N (cases) | AUC (95% CI) | Sensitivity / specificity at 0.5 |", "|---|---:|---|---|"]
    for category, groups in sub["subgroups"].items():
        for label, m in groups.items():
            lines.append(f"| {category}: {label} | {m['n']} ({m['cases']}) | {f(m['auc'])} ({f(m['auc_ci95'][0])} to {f(m['auc_ci95'][1])}) | {f(m['sensitivity_at_0_5'])} / {f(m['specificity_at_0_5'])} |")
    lines.extend(["", "The raw threshold is fixed for description, not a clinical recommendation. No survey weighting, "
                  "subgroup-specific threshold selection, prospective calibration, or fairness certification is claimed."])
    blocks["subgroups"] = "\n".join(lines)
    snapshot = json.loads((ROOT.parents[1] / 'site/app/data/results.json').read_text())['studies'][0]
    data = load_data()
    rows = snapshot['leaderboard']
    sa = next(r for r in rows if r['cohort'] == 'South Africa')
    scopes = snapshot['related_benchmarks']
    blocks['abstract'] = (
        f"We retrospectively audited oral-microbiome diabetes-status prediction in six source studies. "
        f"Removing 129 fecal specimens mislabeled oral leaves 10,228 source specimens (1,251 cases). "
        f"NHANES labels encode self-reported diabetes, not a verified subtype; clinical cohorts use deposited diabetes labels. Related India and Shanghai evaluations exclude their entire corresponding source study. "
        f"Fixed CatBoost yields pooled-source OOF AUC {f(snapshot['reproduces']['cv_auc'])}, "
        f"Portugal AUC {f(ext['Portugal']['full_auc'])}, and South Africa AUC {f(sa['auc'])} "
        f"(conditional 95% interval {f(sa['auc_ci95'][0])}–{f(sa['auc_ci95'][1])}). "
        f"The South African interval includes chance, withdrawing the earlier confident-reversal claim. "
        f"Source-only nested panel selection yields macro-study AUC {f(panel['nested_loso']['macro_auc'])}; "
        f"30 genera do not improve Portugal. A consistent within-study permutation test gives observed "
        f"mean fold AUC {f(perm['observed_auc'])} versus null {f(perm['null_mean'])}, p={perm['p_value']:.4f}. "
        f"Disjoint-row isotonic calibration reduces source ECE from {f(cal['source_oof']['raw']['ece10'])} "
        f"to {f(cal['source_oof']['calibrated']['ece10'])}, but external miscalibration remains. "
        "Subgroup estimates replace training-row scores with OOF evaluation. Association directions vary within "
        "and between countries without identifying a biological or technical cause. All external cohorts informed "
        "development; these are exploratory, not confirmatory estimates. No clinical screening tool, biomarker "
        "panel, validated failure gate, or harm-reduction benefit is established."
    )
    display = json.loads((ROOT / 'docs/Cohort_Display_Contract.json').read_text())['cohorts']
    groups, y = np.asarray(data['study_labels']), np.asarray(data['y_train'])
    for row in display[:6]:
        subset = y[groups == row['key']]
        observed = (len(subset), int(subset.sum()), int((subset == 0).sum()))
        if observed != (row['n'], row['cases'], row['controls']):
            raise ValueError('Cohort presentation counts changed: ' + row['key'])
    dataset = ['Table 1. Cohort identity, specimen, label basis and retained counts.', '',
               '| Cohort / public accession | Specimen | Label basis (case / control) | N (case / control) | Role |',
               '|---|---|---|---:|---|']
    for row in display:
        dataset.append(f"| {row['display']} | {row['specimen']} | {row['label_basis']} | {row['n']} ({row['cases']} / {row['controls']}) | {row['role']} |")
    blocks['dataset'] = '\n'.join(dataset)
    transfer = [f"Pooled-source OOF AUC is {f(snapshot['reproduces']['cv_auc'])}. The descriptive pooled benchmark AUC is "
                f"{f(snapshot['reproduces']['holdout3_auc'])} on 176 specimens, with Shanghai-excluded fitting for its related benchmark.",
                '', 'Table 2. CatBoost transfer and separately fitted within-cohort OOF references. Intervals are conditional.', '',
                '| Cohort | N | Transfer AUC (95% interval) | Within-cohort OOF AUC | Source N |', '|---|---:|---|---:|---:|']
    for r in rows:
        transfer.append(f"| {r['cohort']} | {r['n']} | {f(r['auc'])} ({f(r['auc_ci95'][0])}–{f(r['auc_ci95'][1])}) | {f(r['within_auc'])} | {r['training_scope']['source_n']} |")
    transfer += ['', 'Russia/Moscow AUC ' + f(ext['Russia/Moscow']['full_auc']) + '; related Shanghai AUC ' + f(ext['Shanghai/related']['full_auc']) + '.', '',
                 'South Africa has a below-chance point estimate, but its interval includes 0.5. The historical confident reversal does not survive oral-only reconstruction. Within-cohort structure remains measurable without proving a transferable disease signal.', '',
                 '![Corrected cohort-specific CatBoost transfer estimates with conditional 95% bootstrap intervals. Hollow circles are separately fitted within-cohort OOF estimates without intervals. The dashed line marks chance. India excludes its overlapping source study. South Africa is not distinguishable from chance by this interval.](reports/figures/audited_transfer.png){ width=90% }']
    blocks['transfer'] = '\n'.join(transfer)
    nested = ['Table 3. Outer nested source-study results; inner LOSO selects panel size.', '',
              '| Held source study | N | Inner-selected K | Outer AUC |', '|---|---:|---:|---:|']
    for row in panel['nested_loso']['folds']:
        nested.append(f"| {row['held_study']} | {row['n']} | {row['selected_k']} | {f(row['selected_auc'])} |")
    blocks['nested'] = '\n'.join(nested)
    mp, pt, adapt, ood, props, diversity, pvs = [snapshot[k] for k in ('marker_panel','portability','sign_adaptation','ood_detection','marker_properties','diversity_transfer','population_vs_study')]
    summary = mp['summary']
    investigation = [f"Marker directions: {summary['reversal_prevalence_ex_nhanes']:.0%} of {summary['reversal_tested_ex_nhanes']} informative genera reverse among geographic groups excluding NHANES; {summary['n_robust']} meet the retrospective stable-sign rule and {summary['n_flippers']} meet the broader flipper rule. Different rules produce different denominators.", '',
        f"Portability restriction: mean four-cohort AUC changes from {f(pt['summary']['mean_transfer_full'])} to {f(pt['summary']['mean_transfer_stable'])}. South Africa changes from {f(pt['ablation']['sa_transfer_full'])} to {f(next(r['auc_stable'] for r in pt['loco'] if r['cohort']=='South Africa'))}, remaining below chance as a point estimate. Dropping Atopobium changes it to {f(pt['ablation']['sa_transfer_no_atopobium'])}; the previous beneficial-ablation interpretation is withdrawn.", '',
        f"Local adaptation: South Africa's logistic probe changes from {f(adapt['summary']['sa_transfer'])} with no local labels to {f(adapt['summary']['sa_auc_at_max_k'])} at 40 labels; its within-cohort logistic reference is {f(adapt['summary']['sa_ceiling'])}. These point estimates do not establish clinical calibration or an optimal label requirement.", '',
        f"Distribution diagnostics: domain AUC spans {f(min(r['domain_auc'] for r in ood['cohorts']))} to {f(max(r['domain_auc'] for r in ood['cohorts']))}. Mahalanobis distances are " + ', '.join(f"{r['cohort']} {r['mahalanobis']:.2f}" for r in ood['cohorts']) + '. The largest distance is not proof of a calibrated failure detector.', '',
        f"Marker properties: median source-only prevalence is {props['prevalence']['stable_median']:.1%} for stable genera versus {props['prevalence']['flipper_median']:.1%} for flippers (Mann–Whitney p={props['prevalence']['p']:.4f}). This underpowered association does not qualify a panel.", '',
        f"Diversity: mean transfer AUC is {f(diversity['summary']['mean_diversity_transfer'])} versus {f(diversity['summary']['mean_taxa_transfer'])} for taxa; {diversity['summary']['diversity_reversed_cohorts']}/4 diversity point estimates are below chance.", '',
        f"Study/geography comparison: within-China sign reversals {pvs['sign_flip_rate']['within_china']:.0%} of {pvs['sign_flip_rate']['within_china_n']} informative genera versus cross-geography {pvs['sign_flip_rate']['cross_population']:.0%} of {pvs['sign_flip_rate']['cross_population_n']}. Association-vector correlations average {f(pvs['assoc_vector_correlation']['within_china_mean'])} and {f(pvs['assoc_vector_correlation']['cross_population_mean'])}, respectively. This nested comparison does not estimate a causal variance decomposition."]
    blocks['experiments'] = '\n'.join(investigation)
    path = ROOT / "docs/Preprint.md"
    manuscript = path.read_text()
    for name, content in blocks.items():
        pattern = rf"(<!-- validation:{name}:start -->)\n.*?\n(<!-- validation:{name}:end -->)"
        manuscript, n = re.subn(pattern, lambda m: m[1] + "\n" + content + "\n" + m[2], manuscript, flags=re.S)
        if n != 1:
            raise ValueError(f"Expected one {name} manuscript block, found {n}")
    path.write_text(manuscript)

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlesize": 10, "figure.facecolor": "white", "savefig.facecolor": "white",
                         "svg.hashsalt": "oralbiome-audit-v1"})
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), layout="constrained")
    a, b, c = axes
    x = np.arange(2)
    a.bar(x-.16, [ext[k]["full_auc"] for k in ("Portugal", "three_cohort_pooled")], .32, label="139 genera", color="#334155")
    a.bar(x+.16, [ext[k]["panel30_auc"] for k in ("Portugal", "three_cohort_pooled")], .32, label="30 SHAP genera", color="#0f766e")
    a.set(xticks=x, xticklabels=["Portugal", "Pooled benchmark"], ylim=(0, 1), ylabel="External AUC", title="A. Oral-only source fits")
    a.axhline(.5, linestyle="--", color="#64748b", linewidth=.8)
    a.legend(fontsize=8, loc="lower right")
    full = [r["full_auc"] for r in down["runs"]]
    small = [r["panel30_auc"] for r in down["runs"]]
    b.scatter(full, small, s=16, color="#0f766e", alpha=.7)
    b.plot([.4, .85], [.4, .85], linestyle="--", color="#64748b", linewidth=.8)
    b.set(xlim=(.4,.85), ylim=(.4,.85), xlabel="139 genera: Portugal AUC", ylabel="30 genera: Portugal AUC", title=f"B. {down['n_seeds']} paired sensitivity seeds")
    source = cal["source_oof"]
    cohorts = [source, cal["external_benchmarks"]["holdout"], cal["external_benchmarks"]["holdout_all"]]
    x = np.arange(3)
    c.bar(x-.16, [v["raw"]["ece10"] for v in cohorts], .32, color="#334155", label="Raw")
    c.bar(x+.16, [v["calibrated"]["ece10"] for v in cohorts], .32, color="#0f766e", label="Isotonic")
    c.set(xticks=x, xticklabels=["Source OOF", "Portugal", "Three\ncohorts"], ylim=(0,.5), ylabel="ECE (10 bins)", title="C. Separate calibration / scoring")
    c.legend(fontsize=8)
    fig.savefig(ROOT / "reports/figures/validation_reconstruction.png", dpi=300)
    fig.savefig(ROOT / "reports/figures/validation_reconstruction.svg", metadata={'Date': None})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 3.8), layout='constrained')
    for i, row in enumerate(rows):
        low, high = row['auc_ci95']
        ax.errorbar(row['auc'], i, xerr=[[row['auc']-low], [high-row['auc']]], fmt='o', color='#0f766e', capsize=4,
                    label='Transfer (conditional 95% interval)' if i == 0 else None)
        ax.plot(row['within_auc'], i, 'o', markerfacecolor='none', color='#334155', label='Within-cohort OOF reference' if i == 0 else None)
    ax.set(yticks=range(len(rows)), yticklabels=[r['cohort'] for r in rows], xlim=(0,1), xlabel='AUC', title='Oral-only reconstruction; exploratory benchmarks')
    ax.axvline(.5, color='#64748b', linestyle='--', linewidth=1)
    ax.invert_yaxis()
    ax.legend(loc='lower center', bbox_to_anchor=(.5,-.38), fontsize=8)
    fig.savefig(ROOT / 'reports/figures/audited_transfer.png', dpi=300)
    fig.savefig(ROOT / 'reports/figures/audited_transfer.svg', metadata={'Date': None})
    plt.close(fig)
    for name in ('validation_reconstruction', 'audited_transfer'):
        svg = ROOT / f'reports/figures/{name}.svg'
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    print("Rendered evidence-derived manuscript blocks and reconstruction figure.")


if __name__ == "__main__":
    main()
