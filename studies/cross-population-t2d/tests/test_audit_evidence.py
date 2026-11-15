"""Discriminating controls for the data-free evidence checker."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_audit_evidence as audit


class AuditEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'evidence.json').write_text('{"count": 4}')
        claim = {'observed': 'fixture', 'mechanism': 'fixture', 'correction': 'fixture',
                 'supported': 'fixture', 'remaining_limit': 'fixture',
                 'effect_isolated': False, 'evidence_kind': 'aggregate',
                 'evidence': ['evidence.json'],
                 'assertions': [{'file': 'evidence.json', 'pointer': '/count', 'equals': 4}]}
        self.ledger = {'schema_version': 1, 'scope': 'retained evidence; no isolated correction effects',
                       'evidence': {'evidence.json': hashlib.sha256((self.root/'evidence.json').read_bytes()).hexdigest()},
                       'claims': [dict(copy.deepcopy(claim), id=name) for name in sorted(audit.REQUIRED)]}

    def test_good_evidence_and_retained_ledger(self):
        self.assertEqual(audit.verify(self.root, self.ledger)['aggregate_assertions'], 9)
        actual = json.loads((audit.ROOT/'docs/Audit_Evidence.json').read_text())
        verdict = audit.verify(audit.ROOT, actual)
        self.assertEqual(verdict['claims'], 9)
        self.assertFalse(verdict['source_truth_verified'])

    def test_wrong_number_and_boolean_do_not_pass_as_count(self):
        for value in (5, True, 4.0):
            self.ledger['claims'][0]['assertions'][0]['equals'] = value
            with self.assertRaisesRegex(ValueError, 'Aggregate disagreement'):
                audit.verify(self.root, self.ledger)

    def test_changed_and_missing_evidence(self):
        (self.root/'evidence.json').write_text('{"count": 5}')
        with self.assertRaisesRegex(ValueError, 'Changed evidence'):
            audit.verify(self.root, self.ledger)
        (self.root/'evidence.json').unlink()
        with self.assertRaises(FileNotFoundError):
            audit.verify(self.root, self.ledger)

    def test_missing_field_and_bad_pointer(self):
        for pointer in ('/missing', '/count/missing', 'count'):
            self.ledger['claims'][0]['assertions'][0]['pointer'] = pointer
            with self.assertRaises((ValueError, KeyError, TypeError)):
                audit.verify(self.root, self.ledger)

    def test_missing_duplicate_or_unlinked_claim(self):
        bad = copy.deepcopy(self.ledger); bad['claims'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing or duplicate'):
            audit.verify(self.root, bad)
        bad = copy.deepcopy(self.ledger); bad['claims'][0] = bad['claims'][1]
        with self.assertRaisesRegex(ValueError, 'Missing or duplicate'):
            audit.verify(self.root, bad)
        bad = copy.deepcopy(self.ledger); bad['claims'][0]['evidence'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'Unknown claim evidence'):
            audit.verify(self.root, bad)

    def test_unsupported_scope_and_isolated_effect_rejected(self):
        bad = copy.deepcopy(self.ledger); bad['scope'] = 'clinical validation'
        with self.assertRaisesRegex(ValueError, 'Unsupported audit claim scope'):
            audit.verify(self.root, bad)
        self.ledger['claims'][0]['effect_isolated'] = True
        with self.assertRaisesRegex(ValueError, 'Isolated correction effect'):
            audit.verify(self.root, self.ledger)

    def test_empty_assertion_or_limit_rejected(self):
        bad = copy.deepcopy(self.ledger); bad['claims'][0]['assertions'] = []
        with self.assertRaisesRegex(ValueError, 'no assertions'):
            audit.verify(self.root, bad)
        self.ledger['claims'][0]['remaining_limit'] = ''
        with self.assertRaisesRegex(ValueError, 'Incomplete claim'):
            audit.verify(self.root, self.ledger)

    def test_unsafe_path_and_symlink_rejected(self):
        for path in ('../evidence.json', '/evidence.json', 'a/../evidence.json'):
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                audit.read_evidence(self.root, path)
        (self.root/'link').symlink_to(self.root/'evidence.json')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            audit.read_evidence(self.root, 'link')

    def test_cli_without_site_packages(self):
        result = subprocess.run([sys.executable, '-S', str(audit.ROOT/'scripts/check_audit_evidence.py')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'pass')
        result = subprocess.run([sys.executable, '-S', str(audit.ROOT/'scripts/check_audit_evidence.py'),
                                 '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
