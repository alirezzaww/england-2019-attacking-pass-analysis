"""Offline tests for bin boundaries, probability averaging and absent groups."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('calibration', Path(__file__).resolve().parents[1] / '26_probability_calibration.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def row(identity, probability, goal=0):
    return {'match_id': 1, 'id': identity, 'predicted_probability': probability, 'goal': goal}


class CalibrationTests(unittest.TestCase):
    def test_boundaries_assign_each_prediction_once_including_one(self):
        cases = [(0, 0), (0.0499, 0), (0.05, 1), (0.1, 2), (0.2, 3), (1, 3)]
        for probability, expected in cases:
            with self.subTest(probability=probability):
                self.assertEqual(lesson.probability_bin(probability), expected)
        bins = lesson.calibration_bins([row(str(i), p) for i, (p, _) in enumerate(cases)])
        self.assertEqual(sum(b['shots'] for b in bins), len(cases))

    def test_mean_prediction_and_observed_goal_fraction_are_separate(self):
        group = lesson.calibration_bins([row('a', 0.06, 1), row('b', 0.08, 0)])[1]
        self.assertAlmostEqual(group['mean_predicted_probability'], 0.07)
        self.assertEqual(group['observed_goal_fraction'], 0.5)
        self.assertAlmostEqual(group['predicted_goal_sum'], 0.14)

    def test_absent_group_is_undefined_but_observed_zero_goals_is_zero(self):
        bins = lesson.calibration_bins([row('a', 0.06, 0)])
        self.assertIsNone(bins[0]['mean_predicted_probability'])
        self.assertIsNone(bins[0]['observed_goal_fraction'])
        self.assertEqual(bins[1]['observed_goal_fraction'], 0)

    def test_invalid_probabilities_and_duplicate_shots_are_rejected(self):
        for probability in [-0.1, 1.1, float('nan')]:
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                lesson.probability_bin(probability)
        with self.assertRaises(ValueError):
            lesson.calibration_bins([row('a', 0.1), row('a', 0.1)])


if __name__ == '__main__':
    unittest.main()
