"""Protect fixed evaluation membership and paired shot-weighted match resampling."""
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('frozen_evaluation', ROOT / '27_frozen_model_evaluation.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def summary(n, model, baseline):
    return {'shots': n, 'model_loss_sums': {'log_loss': model, 'brier_score': model},
            'baseline_loss_sums': {'log_loss': baseline, 'brier_score': baseline}}


class FrozenEvaluationTests(unittest.TestCase):
    def test_protocol_excludes_every_development_fixture(self):
        protocol = json.loads((ROOT / 'data/27_evaluation_protocol.json').read_text())
        base = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
        evaluation = set(protocol['evaluation_match_ids'])
        self.assertEqual(protocol['excluded_previously_used_match_ids'], base['match_ids'])
        self.assertEqual(len(evaluation), 45)
        self.assertTrue(evaluation.isdisjoint(base['match_ids']))
        self.assertTrue(protocol['no_refitting'])
        self.assertEqual(protocol['training_shots'], 114)
        self.assertEqual(protocol['frozen_fit']['features'], ['distance_template_m'])
        baseline = protocol['frozen_baseline_fit']
        self.assertEqual(baseline['features'], [])
        self.assertAlmostEqual(1 / (1 + math.exp(-baseline['coefficients'][0])), 11 / 114)

    def test_losses_score_probabilities_without_turning_them_into_labels(self):
        losses = lesson.per_shot_losses(1, 0.8)
        self.assertAlmostEqual(losses['log_loss'], -math.log(0.8))
        self.assertAlmostEqual(losses['brier_score'], 0.04)

    def test_resampling_pools_shot_totals_and_repeats_whole_match_counts(self):
        matches = [summary(1, 0, 1), summary(9, 9, 0)]
        self.assertAlmostEqual(lesson.aggregate_difference(matches, [0, 1], 'log_loss'), 0.8)
        self.assertAlmostEqual(lesson.aggregate_difference(matches, [0, 0, 1], 'log_loss'), 7 / 11)

    def test_paired_identical_models_have_zero_differences(self):
        matches = [summary(1, 0.2, 0.2), summary(9, 3, 3)]
        configuration = {'seed': 42, 'n_resamples': 30}
        differences, invalid = lesson.resample_differences(matches, configuration)
        self.assertEqual(invalid, 0)
        self.assertEqual(differences['log_loss'], [0] * 30)
        self.assertEqual(differences['brier_score'], [0] * 30)
        empty, invalid = lesson.resample_differences([summary(0, 0, 0)], configuration)
        self.assertEqual(invalid, 30)
        self.assertEqual(empty['log_loss'], [])


if __name__ == '__main__':
    unittest.main()
