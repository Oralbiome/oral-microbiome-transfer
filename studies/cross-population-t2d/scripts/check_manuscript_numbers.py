#!/usr/bin/env python3
"""Check the manuscript's key numbers against the persisted validation artifacts.

Dependency-free. Every check pairs a regular expression (which captures the
number(s) printed in docs/Preprint.md) with the value derived from a JSON
artifact. A missing match, a different number, or a different count of matches
fails. This verifies that the prose agrees with retained artifacts; it does not
re-fit any model or certify the artifacts themselves.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = 'data/processed/validation_{}.json'
RESULTS = 'site/app/data/results.json'  # repo-root relative, holds leaderboard intervals
# Statements that need RESULTS. The public release repository has no site/, so these are skipped there.
RESULTS_LABELS = ('South Africa AUC and interval', 'Mexico within-cohort below transfer', 'South Africa secondary estimates')


def f3(x):
    return f'{x:.3f}'


def load(root, name):
    return json.loads((root / DATA.format(name)).read_text())


BASELINE = 'data/processed/baseline_age_sex_v1.json'
BASELINE_CONTROLS = 'data/processed/baseline_age_sex_controls_v1.json'


def d3(x):
    return f'{x:.3f}'.replace('-', '\u2212')


def d4(x):
    return f'{x:.4f}'.replace('-', '\u2212')


def baseline_checks(root):
    """Statements about the preregistered NHANES age-and-sex baseline (Section 4.6 and where it is cited)."""
    base = json.loads((root / BASELINE).read_text())
    ctl = json.loads((root / BASELINE_CONTROLS).read_text())
    if not ctl['all_pass'] or base['decision_C_minus_A'] != 'no evidence microbiome adds beyond age+sex':
        raise ValueError('Baseline artifact no longer supports the manuscript verdict; revise the text')
    a, b, c, cnh = (base['auc'][k] for k in ('A', 'B', 'C', 'C_nh'))
    dca, dba, dnh = (base['delta'][k] for k in ('C_minus_A', 'B_minus_A', 'C_nh_minus_A'))
    st = base['strata']
    ci3 = lambda m: (f3(m['ci95'][0]), f3(m['ci95'][1]))
    return [
        ('baseline abstract AUCs', r'age-and-sex-only logistic model reaches OOF AUC (\d\.\d+) versus (\d\.\d+) for the microbiome-only model, and adding the microbiome to age and sex does not improve it \((\d\.\d+)\)',
         (f3(a['auc']), f3(b['auc']), f3(c['auc'])), 1),
        ('baseline Section 2 AUCs', r'out-of-fold AUC (\d\.\d+), 95% CI (\d\.\d+)\u2013(\d\.\d+), versus (\d\.\d+)\)',
         (f3(a['auc']), *ci3(a), f3(b['auc'])), 1),
        ('baseline C versus A (Sections 2 and 6)', r'\((\d\.\d+); difference (\u2212\d\.\d+), (\u2212\d\.\d+) to (\d\.\d+)\)',
         (f3(c['auc']), d3(dca['delta']), d3(dca['ci95'][0]), d3(dca['ci95'][1])), 1),
        ('baseline C versus A (Section 6)', r'microbiome adds nothing measurable to them \(difference (\u2212\d\.\d+), (\u2212\d\.\d+) to (\d\.\d+)\)',
         (d3(dca['delta']), d3(dca['ci95'][0]), d3(dca['ci95'][1])), 1),
        ('baseline Section 6 A versus B', r'age and sex alone reach a higher out-of-fold AUC \((\d\.\d+)\) than the microbiome \((\d\.\d+)\)',
         (f3(a['auc']), f3(b['auc'])), 1),
        ('baseline Table 5 row A', r'\| A: age \(spline\) \+ sex \| (\d\.\d+) \((\d\.\d+)\u2013(\d\.\d+)\) \|', (f3(a['auc']), *ci3(a)), 1),
        ('baseline Table 5 row B', r'\| B: microbiome only \| (\d\.\d+) \((\d\.\d+)\u2013(\d\.\d+)\) \|', (f3(b['auc']), *ci3(b)), 1),
        ('baseline Table 5 row C', r'\| C: microbiome \+ age \+ sex \| (\d\.\d+) \((\d\.\d+)\u2013(\d\.\d+)\) \|', (f3(c['auc']), *ci3(c)), 1),
        ('baseline C minus A (Section 4.6)', r'changes AUC by (\u2212\d\.\d+) \(95% CI (\u2212\d\.\d+) to (\d\.\d+); C minus A\)',
         (d4(dca['delta']), d4(dca['ci95'][0]), d4(dca['ci95'][1])), 1),
        ('baseline verdict', r'preregistered verdict is "([^"]+)"', (base['decision_C_minus_A'],), 1),
        ('baseline B minus A', r'\(B minus A (\u2212\d\.\d+), (\u2212\d\.\d+) to (\u2212\d\.\d+)\)',
         (d3(dba['delta']), d3(dba['ci95'][0]), d3(dba['ci95'][1])), 1),
        ('baseline NHANES-only sensitivity', r'with age and sex reaches (\d\.\d+) and its difference from A is (\u2212\d\.\d+) \((\u2212\d\.\d+) to (\d\.\d+)\)',
         (f3(cnh['auc']), d4(dnh['delta']), d4(dnh['ci95'][0]), f'{dnh["ci95"][1]:.4f}'), 1),
        ('baseline controls', r'microbiome-only AUC exactly \((\d\.\d+)\); label-permuted models scored near chance \(mean (\d\.\d+) for A and (\d\.\d+) for C, inside the preregistered (\d\.\d+)\u2013(\d\.\d+) range\); '
         r'a synthetic feature with marginal AUC (\d\.\d+) added to A was detected \(difference (\d\.\d+) to (\d\.\d+)\)',
         (f"{ctl['C1']['reproduced_auc_B']:.5f}", f3(ctl['C2']['A_mean']), f3(ctl['C2']['C_mean']), f"{ctl['C2']['range'][0]:.2f}", f"{ctl['C2']['range'][1]:.2f}",
          f3(ctl['C3']['synthetic_marginal_auc']), f3(ctl['C3']['delta_ci95'][0]), f3(ctl['C3']['delta_ci95'][1])), 1),
        ('baseline exploratory strata', r'55\u201365 and 65\+ strata the microbiome-only model ranks above age and sex \((\d\.\d+) versus (\d\.\d+); (\d\.\d+) versus (\d\.\d+)\), '
         r'whereas in the under-40 stratum it ranks below \((\d\.\d+) versus (\d\.\d+)\)',
         (f3(st['age 55-65']['B']), f3(st['age 55-65']['A']), f3(st['age 65+']['B']), f3(st['age 65+']['A']), f3(st['age <40']['B']), f3(st['age <40']['A'])), 1),
        ('baseline stratified cases', r'(\d[\d,]*) rows \((\d+) cases\), one fold split', (f"{base['n']:,}", str(base['cases'])), 1),
    ]


def checks(root):
    """Return (label, regex, expected_tuple, min_matches) for every guarded statement."""
    panel, perm, cal, pooled, sub = (load(root, n) for n in ('panel', 'permutation', 'calibration', 'pooled_oof', 'subgroups'))
    folds = {r['held_study']: r for r in panel['nested_loso']['folds']}
    down, ext_cal = panel['downsample_reconstruction'], cal['external_benchmarks']
    sel = panel['source_selection']['candidates']
    nhanes_share = f"{100 * folds['nhanes']['n'] / sum(r['n'] for r in folds.values()):.1f}"
    out = [
        ('pooled OOF AUC (abstract)', r'pooled-source OOF AUC (\d\.\d+) \(one AUC', (f3(pooled['pooled_oof_auc']),), 1),
        ('pooled OOF AUC (Section 4.1)', r'Pooled-source OOF AUC is (\d\.\d+) \(pooled', (f3(pooled['pooled_oof_auc']),), 1),
        ('nested macro AUC (abstract and 4.1)', r'macro-study nested AUC(?: is)? (\d\.\d+)', (f3(panel['nested_loso']['macro_auc']),), 2),
        ('held-out NHANES AUC', r'held-out NHANES AUC is (\d\.\d+)', (f3(folds['nhanes']['selected_auc']),), 1),
        ('nested macro AUC (Section 3.2)', r'nested macro-study AUC of (\d\.\d+)', (f3(panel['nested_loso']['macro_auc']),), 1),
        ('all-source K selection', r'macro-study AUC (\d\.\d+) versus (\d\.\d+), "all-source selection"',
         (f3(sel['30']['macro_auc']), f3(sel['139']['macro_auc'])), 1),
        ('permutation mean fold AUC', r'(?:observed )?mean fold AUC (\d\.\d+)', (f3(perm['observed_auc']),), 2),
        ('permutation null mean', r'(?:versus null|conditional null mean) (\d\.\d+)', (f3(perm['null_mean']),), 2),
        ('permutation p', r'p=(0\.\d{4})[;.]', (f'{perm["p_value"]:.4f}',), 1),
        ('permutation count', r'none of (\d+) shuffles', (str(perm['n_permutations']),), 1),
        ('calibration ECE (abstract)', r'source ECE(?: \([^)]*\))? from (\d\.\d+) to (\d\.\d+)',
         (f3(cal['source_oof']['raw']['ece10']), f3(cal['source_oof']['calibrated']['ece10'])), 1),
        ('calibration-split raw AUC', r'raw source AUC on these disjoint evaluation rows is (\d\.\d+)', (f3(cal['source_oof']['raw']['auc']),), 1),
        ('Portugal AUC', r'Portugal AUC is (\d\.\d+)', (f3(panel['external_benchmarks']['Portugal']['full_auc']),), 1),
        ('NHANES row share', r'NHANES supplies (\d+\.\d)% of', (nhanes_share,), 1),
        ('NHANES row share (abstract)', r'(\d+\.\d)% of rows are NHANES\)', (nhanes_share,), 1),
        ('source specimens', r'leaves ([\d,]+) source specimens \(([\d,]+) cases\)',
         (f"{panel['eligibility']['source_n']:,}", f"{panel['eligibility']['source_cases']:,}"), 1),
        ('nested versus fixed K=139', r'macro LOSO AUC (\d\.\d+), which is below fixed K=139 across the same six outer studies \((\d\.\d+)\)',
         (f3(panel['nested_loso']['macro_auc']), f3(sel['139']['macro_auc'])), 1),
        ('Portugal 30 versus 139 genera and seeds (abstract)',
         r'\((\d\.\d+) versus (\d\.\d+) for the full fit, but a mean (\d\.\d+) versus (\d\.\d+) across (\d+) downsampled seeds with (\d+)/(\d+) wins\)',
         (f3(panel['external_benchmarks']['Portugal']['panel30_auc']), f3(panel['external_benchmarks']['Portugal']['full_auc']),
          f3(down['panel30']['mean']), f3(down['full']['mean']), str(down['n_seeds']), str(down['panel_wins']), str(down['n_seeds'])), 1),
        ('calibration did not change AUC', r'Calibration did not improve discrimination \(source AUC (\d\.\d+) to (\d\.\d+)\)',
         (f3(cal['source_oof']['raw']['auc']), f3(cal['source_oof']['calibrated']['auc'])), 1),
        ('external ECE Russia and Shanghai', r'Russia/Moscow (\d\.\d+) to (\d\.\d+), related Shanghai (\d\.\d+) to (\d\.\d+);',
         (f3(ext_cal['holdout_664107']['raw']['ece10']), f3(ext_cal['holdout_664107']['calibrated']['ece10']),
          f3(ext_cal['holdout_782768']['raw']['ece10']), f3(ext_cal['holdout_782768']['calibrated']['ece10'])), 1),
        ('Table 2 Russia row', r'\| Russia/Moscow \| (\d+) \| (\d\.\d+) \(interval not computed\)',
         (str(panel['external_benchmarks']['Russia/Moscow']['n']), f3(panel['external_benchmarks']['Russia/Moscow']['full_auc'])), 1),
        ('Table 2 Shanghai row', r'\| Related Shanghai \| (\d+) \| (\d\.\d+) \(interval not computed\)',
         (str(panel['external_benchmarks']['Shanghai/related']['n']), f3(panel['external_benchmarks']['Shanghai/related']['full_auc'])), 1),
        ('age versus sex stratum AUCs', r'within-age-stratum AUCs \((\d\.\d+) to (\d\.\d+), Table 4\) are lower than the within-sex-stratum AUCs \((\d\.\d+) and (\d\.\d+)\)',
         (f3(min(g['auc'] for g in sub['subgroups']['age'].values())), f3(max(g['auc'] for g in sub['subgroups']['age'].values())),
          f3(sub['subgroups']['sex']['Male']['auc']), f3(sub['subgroups']['sex']['Female']['auc'])), 1),
        ('unrounded pooled and mean fold AUC', r'pooled OOF AUC is (\d\.\d{4}) and the mean fold AUC is (\d\.\d{4});',
         (f"{pooled['pooled_oof_auc']:.4f}", f"{pooled['mean_fold_auc']:.4f}"), 1),
    ]
    out += baseline_checks(root)
    results = root.parents[1] / RESULTS
    if results.exists():  # present in the research repository only; see RESULTS_LABELS
        sa = next(r for r in json.loads(results.read_text())['studies'][0]['leaderboard'] if r['cohort'] == 'South Africa')
        out.append(('South Africa AUC and interval',
                    r'South Africa AUC (\d\.\d+) \(conditional 95% interval (\d\.\d+)–(\d\.\d+)\)',
                    (f3(sa['auc']), f3(sa['auc_ci95'][0]), f3(sa['auc_ci95'][1])), 1))
        study = json.loads(results.read_text())['studies'][0]
        mexico = next(r for r in study['leaderboard'] if r['cohort'] == 'Mexico')
        out.append(('Mexico within-cohort below transfer',
                    r'in Mexico the within-cohort OOF AUC \((\d\.\d+)\) is below its transfer AUC \((\d\.\d+)\)',
                    (f3(mexico['within_auc']), f3(mexico['auc'])), 1))
        sa_stable = next(r['auc_stable'] for r in study['portability']['loco'] if r['cohort'] == 'South Africa')
        sa_div = next(c['diversity_transfer'] for c in study['diversity_transfer']['cohorts'] if c['cohort'] == 'South Africa')
        out.append(('South Africa secondary estimates',
                    r'\((\d\.\d+) with the stable-feature restriction, (\d\.\d+) without Atopobium, (\d\.\d+) for the logistic probe with no local labels, (\d\.\d+) for diversity features\)',
                    (f3(sa_stable), f3(study['portability']['ablation']['sa_transfer_no_atopobium']),
                     f3(study['sign_adaptation']['summary']['sa_transfer']), f3(sa_div)), 1))
    return out


def verify(root, manuscript=None):
    text = manuscript if manuscript is not None else (root / 'docs/Preprint.md').read_text()
    verified = 0
    for label, pattern, expected, minimum in checks(root):
        found = re.findall(pattern, text)
        if len(found) < minimum:
            raise ValueError(f'Manuscript statement missing or reworded: {label}')
        for hit in found:
            actual = hit if isinstance(hit, tuple) else (hit,)
            if actual != expected:
                raise ValueError(f'Manuscript disagrees with artifact: {label}: text {actual} vs artifact {expected}')
        verified += len(found)
    skipped = [label for label in RESULTS_LABELS if label not in {c[0] for c in checks(root)}]
    return {'status': 'pass', 'statements_checked': verified, 'skipped_without_site_results': skipped, 'model_rerun': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(json.dumps({'status': 'fail', 'cause': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
