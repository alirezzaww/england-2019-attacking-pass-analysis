"""Offline tests for opening-angle geometry, grouped folds and prediction scoring."""
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('angle_model', Path(__file__).resolve().parents[1] / '25_shot_angle_model.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class ShotAngleTests(unittest.TestCase):
    def test_central_angle_matches_goalpost_geometry_and_mirror_symmetry(self):
        distance, angle = lesson.shot_geometry(100, 40)
        self.assertAlmostEqual(angle, 2 * math.atan(3.66 / distance))
        self.assertEqual(lesson.shot_geometry(100, 30), lesson.shot_geometry(100, 50))

    def test_equal_distance_can_have_different_opening_angles(self):
        central = lesson.shot_geometry(90 * 120 / 105, 34 * 80 / 68)
        wide = lesson.shot_geometry(96 * 120 / 105, 46 * 80 / 68)
        self.assertAlmostEqual(central[0], 15)
        self.assertAlmostEqual(wide[0], 15)
        self.assertGreater(central[1], wide[1])

    def test_invalid_coordinates_and_exact_post_are_rejected(self):
        for coordinates in [(-1, 40), (121, 40), (100, float('nan')), (120, (34 + 3.66) * 80 / 68)]:
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                lesson.shot_geometry(*coordinates)

    def test_folds_keep_every_fixture_out_of_its_own_fitting_rows(self):
        rows = [{'match_id': m, 'id': f'{m}-{j}'} for m in [1, 2, 3] for j in range(2)]
        folds = lesson.leave_one_match_out(rows, [1, 2, 3])
        held = []
        for match_id, fit, validation in folds:
            self.assertNotIn(match_id, {r['match_id'] for r in fit})
            self.assertEqual({r['match_id'] for r in validation}, {match_id})
            held.extend(r['id'] for r in validation)
        self.assertCountEqual(held, [r['id'] for r in rows])
        with self.assertRaises(ValueError):
            lesson.leave_one_match_out(rows, [1, 2])

    def test_scoring_uses_probabilities_instead_of_thresholded_labels(self):
        metrics = lesson.score_predictions([0, 1], [0.25, 0.75])
        self.assertAlmostEqual(metrics['brier_score'], 0.0625)
        self.assertAlmostEqual(metrics['log_loss'], -math.log(0.75))
        with self.assertRaises(ValueError):
            lesson.score_predictions([0], [2])

    def test_prediction_uses_saved_fitting_scaling(self):
        fit = {'features': ['distance_template_m'], 'means': [10], 'scales': [2], 'coefficients': [0, 1]}
        self.assertAlmostEqual(lesson.predict(fit, {'distance_template_m': 14}), 1 / (1 + math.exp(-2)))


if __name__ == '__main__':
    unittest.main()
