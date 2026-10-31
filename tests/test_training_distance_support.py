"""Tests for distance bands, inclusive support boundaries and observed-zero rates."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('distance_support', Path(__file__).resolve().parents[1] / '28_training_distance_support.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class DistanceSupportTests(unittest.TestCase):
    def test_distance_band_boundaries_are_counted_once(self):
        for distance, expected in [(0, 0), (9.999, 0), (10, 1), (20, 2), (30, 3), (55, 3)]:
            with self.subTest(distance=distance):
                self.assertEqual(lesson.distance_band(distance), expected)
        for invalid in [-1, float('nan'), float('inf')]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                lesson.distance_band(invalid)

    def test_training_minimum_and_maximum_are_inside_the_range(self):
        self.assertEqual(lesson.range_category(3.9, 4, 35), lesson.COVERAGE[0])
        self.assertEqual(lesson.range_category(4, 4, 35), lesson.COVERAGE[1])
        self.assertEqual(lesson.range_category(35, 4, 35), lesson.COVERAGE[1])
        self.assertEqual(lesson.range_category(35.1, 4, 35), lesson.COVERAGE[2])
        with self.assertRaises(ValueError):
            lesson.range_category(10, 35, 4)

    def test_empty_group_is_not_the_same_as_observed_zero_goals(self):
        empty = lesson.summarize_group([])
        self.assertIsNone(empty['observed_goal_fraction'])
        self.assertIsNone(empty['min_distance_template_m'])
        observed = lesson.summarize_group([{'match_id': 1, 'id': 'a', 'goal': 0, 'distance_template_m': 25}])
        self.assertEqual(observed['observed_goal_fraction'], 0)
        self.assertEqual(observed['shots'], 1)

    def test_group_rate_uses_goals_over_shots(self):
        rows = [{'match_id': 1, 'id': str(i), 'goal': int(i == 0), 'distance_template_m': d}
                for i, d in enumerate([5, 7, 9])]
        result = lesson.summarize_group(rows)
        self.assertAlmostEqual(result['observed_goal_fraction'], 1 / 3)
        self.assertEqual(result['mean_distance_template_m'], 7)
        self.assertEqual(len(result['shot_ids']), 3)


class PipelineOrderTests(unittest.TestCase):
    def capture_stages(self, extra_args):
        spec = importlib.util.spec_from_file_location('support_pipeline', Path(__file__).resolve().parents[1] / 'scripts/run_research.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with patch.object(runner.sys, 'argv', ['run_research.py', '--headless', *extra_args]), \
                patch.object(runner.subprocess, 'run') as run, patch('builtins.print'):
            runner.main()
        return [Path(call.args[0][1]).name for call in run.call_args_list]

    def test_extended_evaluation_runs_before_its_support_diagnostic(self):
        stages = self.capture_stages(['--extended-evaluation'])
        self.assertLess(stages.index('27_frozen_model_evaluation.py'), stages.index('28_training_distance_support.py'))
        self.assertLess(stages.index('28_training_distance_support.py'), stages.index('check_evidence.py'))

    def test_default_pipeline_uses_saved_evaluation_without_new_download_stage(self):
        stages = self.capture_stages([])
        self.assertNotIn('27_frozen_model_evaluation.py', stages)
        self.assertIn('28_training_distance_support.py', stages)


if __name__ == '__main__':
    unittest.main()
