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
        self.assertGreaterEqual(result['statements_checked'], 29 if result['skipped_without_site_results'] else 32)

    def test_tampered_numbers_fail(self):
        for old, new in [('pooled-source OOF AUC 0.793', 'pooled-source OOF AUC 0.813'),
                         ('mean fold AUC 0.794', 'mean fold AUC 0.793'),
                         ('macro-study AUC 0.684 versus 0.669', 'macro-study AUC 0.684 versus 0.699'),
                         ('NHANES supplies 94.7% of', 'NHANES supplies 84.7% of'),
                         ('(conditional 95% interval 0.323', '(conditional 95% interval 0.223'),
                         ('Russia/Moscow 0.447 to 0.228', 'Russia/Moscow 0.347 to 0.228'),
                         ('(source AUC 0.775 to 0.769)', '(source AUC 0.775 to 0.779)'),
                         ('(0.576 to 0.608, Table 4)', '(0.476 to 0.608, Table 4)'),
                         ('0.486 with the stable-feature restriction', '0.586 with the stable-feature restriction')]:
            if old.startswith(('0.486', '(conditional')) and gate.RESULTS_LABELS[0] not in LABELS:
                continue  # needs site results.json, absent from the public release repository
            self.assertIn(old, TEXT, old)
            with self.assertRaisesRegex(ValueError, 'disagrees with artifact'):
                gate.verify(gate.ROOT, TEXT.replace(old, new))

    def test_new_statements_are_guarded(self):
        for label in ('Table 2 Russia row', 'Table 2 Shanghai row', 'age versus sex stratum AUCs'):
            self.assertIn(label, LABELS)
        if gate.RESULTS_LABELS[0] in LABELS:
            for label in gate.RESULTS_LABELS:
                self.assertIn(label, LABELS)
        else:
            self.assertEqual(gate.verify(gate.ROOT)['skipped_without_site_results'], list(gate.RESULTS_LABELS))

    def test_removed_statement_fails(self):
        with self.assertRaisesRegex(ValueError, 'missing or reworded'):
            gate.verify(gate.ROOT, TEXT.replace('held-out NHANES AUC is', 'held-out NHANES result is'))

    def test_command_line_exit_codes(self):
        ok = subprocess.run([sys.executable, str(gate.ROOT / 'scripts/check_manuscript_numbers.py')], capture_output=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)


if __name__ == '__main__':
    unittest.main()
