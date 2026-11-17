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
