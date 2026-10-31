"""Protect the distinction between pass, shot and possession identities."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('shot_units', Path(__file__).resolve().parents[1] / '24_passes_shots_and_possessions.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def row(identity, shot='s1', possession=7, xg=0.2, match=1):
    return {'match_id': match, 'id': identity, 'shot_id': shot, 'period': 1,
            'possession': possession, 'shot_xg': xg}


class ShotUnitTests(unittest.TestCase):
    def test_two_passes_before_one_shot_do_not_double_its_xg(self):
        result = lesson.summarize_units([row('p1'), row('p2')])
        self.assertEqual(result['qualifying_passes'], 2)
        self.assertEqual(result['distinct_assigned_shots'], 1)
        self.assertEqual(result['assigned_shot_xg_counted_once'], 0.2)
        self.assertEqual(result['incorrect_repeated_shot_xg_sum_for_demonstration'], 0.4)

    def test_one_possession_can_contain_two_distinct_shots(self):
        result = lesson.summarize_units([row('p1'), row('p2', shot='s2', xg=0.1)])
        self.assertEqual(result['distinct_assigned_shots'], 2)
        self.assertEqual(result['distinct_possessions'], 1)
        self.assertAlmostEqual(result['assigned_shot_xg_counted_once'], 0.3)

    def test_repeated_pass_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            lesson.summarize_units([row('p1'), row('p1')])

    def test_conflicting_metadata_for_one_shot_is_rejected(self):
        with self.assertRaises(ValueError):
            lesson.summarize_units([row('p1'), row('p2', xg=0.3)])
        # Same identifiers from different fixtures are separate units.
        result = lesson.summarize_units([row('p1'), row('p1', match=2)])
        self.assertEqual(result['distinct_assigned_shots'], 2)


if __name__ == '__main__':
    unittest.main()
