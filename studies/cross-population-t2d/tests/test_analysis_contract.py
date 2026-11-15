"""Data-free checks of the original analysis functions shipped in the package."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import calibrate
import reconstruct_validation as validation
from transfer_contract import training_mask
import transfer_contract


class AnalysisContractTests(unittest.TestCase):
    def test_full_shap_ranking_excludes_base_column(self):
        class Model:
            def get_feature_importance(self, pool, type):
                return np.tile(np.r_[np.arange(139), 9999], (6, 1))
        order, importance = validation.shap_order(Model(), np.zeros((6, 139)), np.array([0, 1] * 3))
        self.assertEqual(order[0], 138)
        self.assertEqual(set(order), set(range(139)))
        self.assertEqual(len(importance), 139)

    def test_study_selection_never_fits_validation_rows(self):
        seen = []
        outer = self
        class Model:
            def fit(self, X, y):
                self.ids = set(X[:, 0])
                return self
            def predict_proba(self, X):
                outer.assertFalse(self.ids & set(X[:, 0]))
                seen.append(True)
                p = (X[:, 0] % 2) * .8 + .1
                return np.c_[1-p, p]
        X = np.repeat(np.arange(24)[:, None], 139, axis=1)
        with patch.object(validation, "model", side_effect=Model), patch.object(
                validation, "shap_order", return_value=(np.arange(139), np.ones(139))):
            choice, scores = validation.study_select(X, np.arange(24) % 2, np.repeat(["a", "b", "c"], 8))
        self.assertEqual(len(seen), 6)
        self.assertEqual(choice, 139)
        self.assertEqual(scores["30"]["macro_auc"], 1)

    def test_conditional_shuffle_preserves_group_case_counts(self):
        y = np.array([0, 0, 1, 1, 0, 1, 1, 1])
        groups = np.repeat(["a", "b"], 4)
        shuffled = validation.permute_within_studies(y, groups, np.random.default_rng(42))
        for group in np.unique(groups):
            self.assertEqual(y[groups == group].sum(), shuffled[groups == group].sum())

    def test_ece_endpoints_and_wrong_predictions(self):
        self.assertEqual(validation.ece(np.array([0, 1]), np.array([0., 1.])), 0)
        self.assertEqual(validation.ece(np.array([1, 0]), np.array([0., 1.])), 1)

    def test_invalid_counts_rejected(self):
        for value in (float("nan"), -1):
            with self.assertRaisesRegex(ValueError, "nonnegative"):
                calibrate.rank_transform(pd.DataFrame({"genus": [value]}), ["genus"])

    def test_whole_related_studies_excluded(self):
        data = {"study_labels": np.array(["nhanes", "india_source", "china_shanghai_t2dm", "other"])}
        np.testing.assert_array_equal(training_mask(data, "India/Mumbai"), [True, False, True, True])
        np.testing.assert_array_equal(training_mask(data, "Shanghai/related"), [True, True, False, True])

    def test_real_identity_guard_accepts_exclusion_and_rejects_overlap(self):
        # Deliver on-disk fixtures through the real input reader and guard.
        # Only the deliberately broken source mask is patched for the bad case.
        data = {'study_labels': pd.Series(['india_source', 'other'],
                                          index=['fixture_shared', 'fixture_source']),
                'feature_names': ['genus_a', 'genus_b']}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pd.DataFrame({'genus_a': [1, 2], 'genus_b': [2, 1]},
                         index=['fixture_shared', 'fixture_eval']).to_csv(root/'counts.csv')
            (root/'labels.tsv').write_text('fixture_shared\t1\nfixture_eval\t0\n')
            with patch.object(transfer_contract, 'ROOT', root):
                X, y = transfer_contract.external_rows(data, 'India/Mumbai', 'counts.csv', 'labels.tsv')
                self.assertEqual(X.shape, (2, 2))
                np.testing.assert_array_equal(y, [1, 0])
                with patch.object(transfer_contract, 'training_mask', return_value=np.ones(2, dtype=bool)):
                    with self.assertRaisesRegex(ValueError, 'overlap model-fitting rows'):
                        transfer_contract.external_rows(data, 'India/Mumbai', 'counts.csv', 'labels.tsv')


if __name__ == "__main__":
    unittest.main()
