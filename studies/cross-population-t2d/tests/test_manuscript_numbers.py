"""The manuscript-number gate must pass on the real manuscript and fail on tampering."""
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_manuscript_numbers as gate

TEXT = (gate.ROOT / 'docs/Preprint.md').read_text()
LABELS = [c[0] for c in gate.checks(gate.ROOT)]


class ManuscriptNumberTests(unittest.TestCase):
    def test_real_manuscript_matches_artifacts(self):
        result = gate.verify(gate.ROOT)
        self.assertEqual(result['status'], 'pass')
        self.assertGreaterEqual(result['statements_checked'], 56 if result['skipped_without_site_results'] else 59)

    def test_tampered_numbers_fail(self):
        for old, new in [('pooled-source OOF AUC 0.793', 'pooled-source OOF AUC 0.813'),
                         ('mean fold AUC 0.794', 'mean fold AUC 0.793'),
                         ('macro-study AUC 0.684 versus 0.669', 'macro-study AUC 0.684 versus 0.699'),
                         ('NHANES supplies 94.7% of', 'NHANES supplies 84.7% of'),
                         ('(conditional 95% interval 0.323', '(conditional 95% interval 0.223'),
                         ('Russia/Moscow 0.447 to 0.228', 'Russia/Moscow 0.347 to 0.228'),
                         ('(source AUC 0.775 to 0.769)', '(source AUC 0.775 to 0.779)'),
                         ('(0.576 to 0.608, Table 4)', '(0.476 to 0.608, Table 4)'),
                         ('0.486 with the stable-feature restriction', '0.586 with the stable-feature restriction'),
                         ('| A: age (spline) + sex | 0.803 (0.790', '| A: age (spline) + sex | 0.813 (0.790'),
                         ('versus 0.698 for the microbiome-only model', 'versus 0.798 for the microbiome-only model'),
                         ('changes AUC by \u22120.0011 (95% CI \u22120.0093 to 0.0072; C minus A)', 'changes AUC by \u22120.0011 (95% CI \u22120.0093 to 0.0172; C minus A)'),
                         ('; 0.597 versus 0.476)', '; 0.597 versus 0.576)'),
                         ('mean 0.492 for A', 'mean 0.592 for A'),
                         ('| Age 65+ (n 610; 163 cases) | 0.476 |', '| Age 65+ (n 610; 163 cases) | 0.576 |'),
                         ('| Female (n 4815; 405 cases) | 0.807 | 0.707 | 0.807 |', '| Female (n 4815; 405 cases) | 0.807 | 0.707 | 0.907 |'),
                         ('age-and-sex model (OOF AUC 0.803) discriminates better', 'age-and-sex model (OOF AUC 0.703) discriminates better'),
                         ('bounds any gain at about +0.007 AUC', 'bounds any gain at about +0.017 AUC'),
                         ('NHANES-only C (0.794) falls below A', 'NHANES-only C (0.804) falls below A'),
                         ('below-0.5 AUC in the 65+ stratum (0.476)', 'below-0.5 AUC in the 65+ stratum (0.576)'),
                         ('The interval includes 0, so the preregistered verdict is "no evidence microbiome adds beyond age+sex"', 'The interval includes 0, so the preregistered verdict is "microbiome adds discrimination beyond age+sex in NHANES"')]:
            if old.startswith(('0.486', '(conditional')) and gate.RESULTS_LABELS[0] not in LABELS:
                continue  # needs site results.json, absent from the public release repository
            self.assertIn(old, TEXT, old)
            with self.assertRaisesRegex(ValueError, 'disagrees with artifact'):
                gate.verify(gate.ROOT, TEXT.replace(old, new))

    def test_new_statements_are_guarded(self):
        for label in ('Table 2 Russia row', 'Table 2 Shanghai row', 'age versus sex stratum AUCs', 'baseline abstract AUCs',
                      'baseline Table 5 row A', 'baseline C minus A (Section 4.6)', 'baseline verdict', 'baseline controls', 'baseline exploratory strata', 'baseline Table 6 age 65+', 'baseline gain bound (Sections 4.6 and 6)'):
            self.assertIn(label, LABELS)
        if gate.RESULTS_LABELS[0] in LABELS:
            for label in gate.RESULTS_LABELS:
                self.assertIn(label, LABELS)
        else:
            self.assertEqual(gate.verify(gate.ROOT)['skipped_without_site_results'], list(gate.RESULTS_LABELS))

    def test_baseline_artifact_contradicting_verdict_fails(self):
        import json
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data/processed').mkdir(parents=True)
            for name in ('validation_panel', 'validation_permutation', 'validation_calibration', 'validation_pooled_oof', 'validation_subgroups',
                         'baseline_age_sex_v1', 'baseline_age_sex_controls_v1'):
                shutil.copy(gate.ROOT / f'data/processed/{name}.json', root / f'data/processed/{name}.json')
            controls = json.loads((root / 'data/processed/baseline_age_sex_controls_v1.json').read_text())
            controls['all_pass'] = False
            (root / 'data/processed/baseline_age_sex_controls_v1.json').write_text(json.dumps(controls))
            with self.assertRaisesRegex(ValueError, 'no longer supports the manuscript verdict'):
                gate.baseline_checks(root)

    def test_baseline_strata_contradicting_wording_fails(self):
        import json
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data/processed').mkdir(parents=True)
            for name in ('validation_panel', 'validation_permutation', 'validation_calibration', 'validation_pooled_oof', 'validation_subgroups',
                         'baseline_age_sex_v1', 'baseline_age_sex_controls_v1'):
                shutil.copy(gate.ROOT / f'data/processed/{name}.json', root / f'data/processed/{name}.json')
            base = json.loads((root / 'data/processed/baseline_age_sex_v1.json').read_text())
            base['strata']['age 65+']['A'] = 0.6  # A no longer below 0.5: the "not investigated below-0.5" wording would be false
            (root / 'data/processed/baseline_age_sex_v1.json').write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError, 'no longer support the stratum and learner wording'):
                gate.baseline_checks(root)

    def test_removed_statement_fails(self):
        with self.assertRaisesRegex(ValueError, 'missing or reworded'):
            gate.verify(gate.ROOT, TEXT.replace('held-out NHANES AUC is', 'held-out NHANES result is'))

    def test_command_line_exit_codes(self):
        ok = subprocess.run([sys.executable, str(gate.ROOT / 'scripts/check_manuscript_numbers.py')], capture_output=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)


if __name__ == '__main__':
    unittest.main()
