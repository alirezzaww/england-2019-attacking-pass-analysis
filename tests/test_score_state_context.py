"""Protect pre-event score labels, event ordering and goal accounting."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('score_context', Path(__file__).resolve().parents[1] / '22_score_state_context.py')
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


def event(index, kind='Pass', team=1, period=1):
    record = {'id': f'e{index}', 'index': index, 'period': period, 'minute': 10, 'second': 0,
              'team': {'id': team}, 'type': {'name': kind}}
    if kind == 'Shot':
        record['shot'] = {'outcome': {'name': 'Goal'}}
    return record


def passes(*indices):
    return [{'id': f'e{i}', 'match_id': 99, 'player_id': 7, 'qualifying': False} for i in indices]


class ScoreStateTests(unittest.TestCase):
    def test_goal_does_not_leak_backwards_into_passes_before_it(self):
        # All events share the same nominal clock; event index must resolve order.
        events = [event(3), event(2, 'Shot'), event(1)]
        tagged, goals, final = lesson.annotate_match(events, passes(1, 3), 1, 2)
        self.assertEqual([p['state'] for p in tagged], ['Drawing', 'Leading'])
        self.assertEqual([p['england_goals_before'] for p in tagged], [0, 1])
        self.assertEqual(final, [1, 0])
        self.assertEqual(goals[0]['score_before'], [0, 0])

    def test_halftime_keeps_score_and_shootout_does_not_change_it(self):
        events = [event(1, 'Shot'), event(2, period=2), event(3, 'Shot', team=2, period=5)]
        tagged, _, final = lesson.annotate_match(events, passes(2), 1, 2)
        self.assertEqual(tagged[0]['state'], 'Leading')
        self.assertEqual(final, [1, 0])

    def test_own_goal_pair_counts_once_for_the_correct_opponent(self):
        events = [event(1, 'Own Goal Against'), event(2, 'Own Goal For', team=2), event(3)]
        tagged, goals, final = lesson.annotate_match(events, passes(3), 1, 2)
        self.assertEqual(final, [0, 1])
        self.assertEqual(len(goals), 1)
        self.assertEqual(tagged[0]['state'], 'Trailing')

    def test_unobserved_state_is_undefined_instead_of_zero(self):
        summary = lesson.summarize([{'state': 'Leading', 'qualifying': False}])
        self.assertEqual(summary[0]['qualifying_share_pct'], 0)
        self.assertIsNone(summary[1]['qualifying_share_pct'])
        self.assertEqual(lesson.score_state(1, 1), 'Drawing')


if __name__ == '__main__':
    unittest.main()
