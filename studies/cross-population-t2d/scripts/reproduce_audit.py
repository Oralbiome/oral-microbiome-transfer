#!/usr/bin/env python3
"""Fail-fast reproduction of current claims, not the archived exploratory sweeps.

Use --experiments-only when the four validation artifacts have just been rebuilt.
This does not download or rerun restricted NHANES raw reads.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ['marker_stability', 'portability', 'sign_adaptation', 'ood_detection',
               'marker_properties', 'diversity_transfer', 'population_vs_study']


def run(script, *args):
    print(f"Running {script}", flush=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiments-only', action='store_true')
    args = parser.parse_args()
    if not args.experiments_only:
        run('reconstruct_validation.py')
    run('reconstruct_subgroups.py')
    for name in EXPERIMENTS:
        run(f'experiment_{name}.py')
    run('calibrate.py', 'export')
    # Manuscript result blocks must exist before these rendering steps.
    run('build_site_data.py', '--write-pooled-oof')
    run('render_validation.py')
    run('render_preprint.py')


if __name__ == '__main__':
    main()
