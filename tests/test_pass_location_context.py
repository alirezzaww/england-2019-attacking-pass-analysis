"""Small, offline tests for zone boundaries and missing/pooled denominators."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pass_location', ROOT / '20_pass_location_context.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class LocationSummaryTests(unittest.TestCase):
    def test_boundary_points_are_counted_once(self):
        cases = [(0, 0), (39.999, 0), (40, 1), (79.999, 1), (80, 2), (120, 2)]
        for coordinate, index in cases:
            with self.subTest(x=coordinate):
                self.assertEqual(lesson.starting_third(coordinate), lesson.ZONES[index])
        for invalid in [-0.1, 120.1, float('nan'), float('inf'), None]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    lesson.starting_third(invalid)

    def test_no_passes_is_undefined_but_no_selected_passes_is_zero(self):
        players = [{'player_id': 1, 'player_name': 'Example'}]
        rows = lesson.summarize([{'player_id': 1, 'zone': lesson.ZONES[1], 'qualifying': False}], players)
        self.assertIsNone(rows[0]['zones'][0]['qualifying_share_pct'])
        self.assertEqual(rows[0]['zones'][1]['qualifying_share_pct'], 0)
        absent = lesson.summarize([], players)[0]
        self.assertIsNone(absent['overall_qualifying_share_pct'])
        self.assertTrue(all(row['pass_start_mix_pct'] is None for row in absent['zones']))

    def test_overall_share_pools_counts_instead_of_averaging_zone_percentages(self):
        passes = [{'player_id': 1, 'zone': lesson.ZONES[0], 'qualifying': True}]
        passes += [{'player_id': 1, 'zone': lesson.ZONES[1], 'qualifying': False} for _ in range(3)]
        row = lesson.summarize(passes, [{'player_id': 1, 'player_name': 'Example'}])[0]
        self.assertEqual(row['overall_qualifying_share_pct'], 25)
        self.assertEqual(row['zones'][0]['pass_start_mix_pct'], 25)
        self.assertEqual(row['zones'][1]['pass_start_mix_pct'], 75)


if __name__ == '__main__':
    unittest.main()
