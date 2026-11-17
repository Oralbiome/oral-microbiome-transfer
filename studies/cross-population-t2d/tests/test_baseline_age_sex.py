import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import baseline_age_sex as b


class BaselineAgeSexTests(unittest.TestCase):
    def test_spline_linear_in_tails_and_shape(self):
        age = np.linspace(1, 80, 200)
        k = b.knots_from(age)
        self.assertEqual(b.rcs_basis(age, k).shape, (200, 3))
        tail = b.rcs_basis(np.array([90., 100., 110.]), k)
        self.assertTrue(np.allclose(np.diff(tail, 2, axis=0), 0, atol=1e-9))

    def test_knots_use_training_rows_only(self):
        train = np.arange(20, 60, dtype=float)
        test = np.array([1., 2., 99.])
        _, knots = b.fit_predict_A(train, np.zeros(40), (train > 45).astype(int), test, np.zeros(3))
        self.assertTrue(np.allclose(knots, np.percentile(train, b.KNOT_PCT)))
        self.assertGreater(knots[0], 20)  # extreme test ages never entered the knots

    def test_age_signal_recovered_and_no_signal_is_chance(self):
        rng = np.random.default_rng(0)
        age = rng.uniform(5, 80, 4000)
        sex = rng.integers(0, 2, 4000).astype(float)
        y = (rng.random(4000) < 1 / (1 + np.exp(-(age - 50) / 8))).astype(int)
        p, _ = b.fit_predict_A(age[:3000], sex[:3000], y[:3000], age[3000:], sex[3000:])
        self.assertGreater(b.auc(y[3000:], p), 0.75)
        ynull = rng.integers(0, 2, 4000)
        p, _ = b.fit_predict_A(age[:3000], sex[:3000], ynull[:3000], age[3000:], sex[3000:])
        self.assertLess(abs(b.auc(ynull[3000:], p) - 0.5), 0.06)

    def test_leak_guard(self):
        b.assert_no_leak([(np.array([0, 1]), np.array([2])), (np.array([2]), np.array([0, 1]))], 3)
        with self.assertRaises(AssertionError):
            b.assert_no_leak([(np.array([0, 1]), np.array([1, 2]))], 3)

    def test_paired_bootstrap_identical_models_zero_difference(self):
        rng = np.random.default_rng(1)
        y = (rng.random(400) < .2).astype(int)
        s = rng.normal(size=400) + y
        d = b.paired_bootstrap(y, {"a": s, "b": s.copy()}, reps=50)
        self.assertTrue(np.allclose(d["a"], d["b"]))
        self.assertEqual(d["a"].shape, (50,))

    def test_paired_bootstrap_detects_better_model(self):
        rng = np.random.default_rng(2)
        y = (rng.random(600) < .3).astype(int)
        good, noise = rng.normal(size=600) + 1.5 * y, rng.normal(size=600)
        d = b.paired_bootstrap(y, {"g": good, "n": noise}, reps=200)
        self.assertGreater(b.ci(d["g"] - d["n"])[0], 0)

    def test_decision_rule(self):
        self.assertIn("adds discrimination", b.decide(0.01, 0.03))
        self.assertEqual(b.decide(-0.009, 0.007), "no evidence microbiome adds beyond age+sex")
        self.assertEqual(b.decide(-0.03, -0.01), "adding microbiome hurts")
        self.assertIn("no better", b.b_vs_a_reading(-0.1, -0.12, -0.08))
        self.assertIn("better than", b.b_vs_a_reading(0.05, 0.01, 0.09))
        self.assertIn("inconclusive", b.b_vs_a_reading(0.02, -0.01, 0.05))


if __name__ == "__main__":
    unittest.main()
