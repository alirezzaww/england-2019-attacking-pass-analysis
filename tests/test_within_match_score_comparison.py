"""Check fixture overlap based on exposure, missing comparisons and pooled ratios."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('within_match', Path(__file__).resolve().parents[1] / '23_within_match_score_comparison.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def rows(match, state, n, k):
    return [{'match_id': match, 'state': state, 'qualifying': i < k} for i in range(n)]


class WithinMatchTests(unittest.TestCase):
    def test_zero_qualifying_events_do_not_remove_an_observed_state(self):
        passes = rows(1, 'Drawing', 10, 0) + rows(1, 'Trailing', 5, 1)
        result = lesson.compare_states(passes, [1], 'Drawing', 'Trailing')
        self.assertEqual(result['common_match_ids'], [1])
        self.assertEqual(result['common_fixture_pool'][0]['qualifying_share_pct'], 0)
        self.assertEqual(result['common_difference_second_minus_first_pp'], 20)

    def test_no_common_fixture_returns_an_undefined_comparison(self):
        passes = rows(1, 'Leading', 10, 1) + rows(2, 'Trailing', 5, 1)
        result = lesson.compare_states(passes, [1, 2], 'Leading', 'Trailing')
        self.assertEqual(result['common_match_ids'], [])
        self.assertIsNone(result['common_difference_second_minus_first_pp'])
        self.assertTrue(all(cell['qualifying_share_pct'] is None for cell in result['common_fixture_pool']))

    def test_common_pool_sums_counts_instead_of_averaging_fixture_percentages(self):
        passes = rows(1, 'Drawing', 1, 1) + rows(2, 'Drawing', 9, 0)
        passes += rows(1, 'Trailing', 2, 1) + rows(2, 'Trailing', 8, 0)
        # Fixture 3 has only one state and must not enter the restricted pool.
        passes += rows(3, 'Drawing', 5, 5)
        result = lesson.compare_states(passes, [1, 2, 3], 'Drawing', 'Trailing')
        self.assertEqual(result['common_match_ids'], [1, 2])
        self.assertEqual(result['common_fixture_pool'][0]['qualifying_share_pct'], 10)
        self.assertEqual(result['common_difference_second_minus_first_pp'], 0)
        self.assertEqual(result['all_fixture_pool'][0]['qualifying_passes'], 6)


if __name__ == '__main__':
    unittest.main()
