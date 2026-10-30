"""Tests for paired match resampling, pooled ratios and undefined exposure."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('match_bootstrap', Path(__file__).resolve().parents[1] / '21_match_bootstrap_uncertainty.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def row(k1, n1, k2, n2):
    return {'players': [{'qualifying_passes': k1, 'eligible_completed_passes': n1},
                        {'qualifying_passes': k2, 'eligible_completed_passes': n2}]}


class MatchBootstrapTests(unittest.TestCase):
    def test_both_players_receive_the_same_match_draw(self):
        rows = [row(1, 2, 1, 2), row(0, 10, 0, 10), row(3, 4, 3, 4)]
        differences, invalid, example = lesson.paired_bootstrap(rows, n_resamples=100, seed=7)
        self.assertEqual(invalid, 0)
        self.assertEqual(differences, [0] * 100)
        self.assertEqual(len(example), len(rows))

    def test_repeated_matches_repeat_both_numerator_and_denominator(self):
        rows = [row(1, 1, 0, 1), row(0, 9, 0, 9)]
        self.assertEqual(lesson.pooled_share(rows, [0, 1], 0), 10)
        self.assertAlmostEqual(lesson.pooled_share(rows, [0, 0, 1], 0), 200 / 11)

    def test_zero_exposure_is_reported_instead_of_imputed_as_zero_share(self):
        rows = [row(0, 0, 1, 2)]
        self.assertIsNone(lesson.pooled_share(rows, [0], 0))
        differences, invalid, _ = lesson.paired_bootstrap(rows, n_resamples=10, seed=7)
        self.assertEqual(differences, [])
        self.assertEqual(invalid, 10)

    def test_percentile_uses_documented_linear_interpolation(self):
        self.assertEqual(lesson.percentile([10, 0], 0.25), 2.5)
        self.assertEqual(lesson.percentile([10, 0], 0), 0)
        self.assertEqual(lesson.percentile([10, 0], 1), 10)
        with self.assertRaises(ValueError):
            lesson.percentile([], 0.5)


if __name__ == '__main__':
    unittest.main()
