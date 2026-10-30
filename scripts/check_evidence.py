"""Offline consistency checks for the saved research artifacts (standard library only)."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT / 'data' / name).read_text())

def ids(rows):
    values = {(r['match_id'], r['id']) for r in rows}
    assert len(values) == len(rows), 'Duplicate selected pass identity'
    return values

base = read('11_tournament_passes_evidence.json')
timed = read('13_minutes_and_quality_evidence.json')
sensitivity = read('14_threshold_sensitivity_evidence.json')
profile = read('15_kirby_profile_evidence.json')
variation = read('16_match_variation_evidence.json')
volume = read('17_passing_volume_evidence.json')
model = read('18_first_xg_model_evidence.json')
manifest = read('source_manifest.json')

assert base['games'] == len(set(base['match_ids'])) == 7
assert len(base['selected_passes']) == base['total_qualifying_passes'] == 200
assert sum(base['per_match_counts'].values()) == 200
assert sum(map(sum, base['raw_zone_counts'])) == 200
assert math.isclose(sum(map(sum, base['zone_rates_per_game'])), 200 / 7)
counts = Counter(str(p['match_id']) for p in base['selected_passes'])
assert all(counts[k] == value for k, value in base['per_match_counts'].items())
assert ids(base['selected_passes']) == ids(timed['all_qualifying_passes'])

low = sensitivity['selected_passes']['0.07']
high = sensitivity['selected_passes']['0.10']
assert len(low) == 113 and len(high) == 98
assert ids(high) <= ids(low) <= ids(base['selected_passes'])
assert ids(low) == ids(timed['passes_before_shots_above_threshold'])
for rows, threshold in [(low, 0.07), (high, 0.10)]:
    assert all(p['shot_xg'] > threshold and 0 <= p['seconds_before_shot'] <= 15 for p in rows)

interval_minutes = defaultdict(float)
match_minutes = defaultdict(float)
for interval in timed['player_intervals']:
    value = (interval['end_seconds'] - interval['start_seconds']) / 60
    assert value > 0 and math.isclose(value, interval['minutes'])
    interval_minutes[interval['player_id']] += value
    match_minutes[interval['match_id']] += value
for audit in timed['match_audits']:
    expected = 11 * audit['match_minutes'] - audit['sending_off_or_permanent_departure_seconds_lost'] / 60
    assert math.isclose(match_minutes[audit['match_id']], expected)
for p in timed['players']:
    assert p['minutes'] > 0 and math.isclose(p['minutes'], interval_minutes[p['player_id']])
    assert math.isclose(p['all_qualifying_per90'], p['all_qualifying'] / p['minutes'] * 90)
assert sum(p['all_qualifying'] for p in timed['players']) == 200
for suffix, rows in [('007', low), ('010', high)]:
    per_player = Counter(p['player_id'] for p in rows)
    for p in sensitivity['players']:
        assert p[f'count_{suffix}'] == per_player[p['player_id']]
        assert math.isclose(p[f'per90_{suffix}'], p[f'count_{suffix}'] / p['minutes'] * 90)

rows = profile['selected_passes']
assert len(rows) == 12
assert ids(rows) == ids([p for p in high if p['player_name'] == profile['player']])
assert profile['forward'] == sum(p['end_x'] > p['x'] for p in rows) == 10
assert profile['backward'] == sum(p['end_x'] < p['x'] for p in rows) == 2
assert profile['final_third_starts'] == sum(p['x'] >= 80 for p in rows) == 9
assert profile['final_third_entries'] == sum(p['x'] < 80 <= p['end_x'] for p in rows) == 2

match_rows = variation['matches']
assert {r['match_id'] for r in match_rows} == set(base['match_ids'])
assert sum(r['qualifying_passes'] for r in match_rows) == variation['total_passes'] == 12
player_intervals = [r for r in timed['player_intervals'] if r['player_name'] == variation['player']]
for row in match_rows:
    expected_minutes = sum(r['minutes'] for r in player_intervals if r['match_id'] == row['match_id'])
    expected_count = sum(r['match_id'] == row['match_id'] and r['player_name'] == variation['player'] for r in high)
    assert row['qualifying_passes'] == expected_count
    assert math.isclose(row['minutes'], expected_minutes)
    if row['minutes'] == 0:
        assert row['per90'] is None and row['qualifying_passes'] == 0
    else:
        assert math.isclose(row['per90'], expected_count / expected_minutes * 90)
assert math.isclose(sum(r['minutes'] for r in match_rows), variation['total_minutes'])
assert math.isclose(variation['tournament_per90'], 12 / variation['total_minutes'] * 90)
for row in variation['leave_one_appearance_out']:
    omitted = next(r for r in match_rows if r['match_id'] == row['omitted_match_id'])
    assert omitted['minutes'] > 0
    assert row['remaining_passes'] == 12 - omitted['qualifying_passes']
    assert math.isclose(row['remaining_minutes'], variation['total_minutes'] - omitted['minutes'])
    assert math.isclose(row['per90'], row['remaining_passes'] / row['remaining_minutes'] * 90)

assert set(volume['match_ids']) == set(base['match_ids'])
assert sum(p['qualifying_passes'] for p in volume['players']) == volume['qualifying_passes_total'] == 98
assert sum(p['eligible_completed_passes'] for p in volume['players']) == volume['eligible_passes_total'] == 2837
selected_counts = Counter(p['player_id'] for p in high)
for row in volume['players']:
    assert row['qualifying_passes'] == selected_counts[row['player_id']]
    assert row['eligible_completed_passes'] >= row['qualifying_passes']
    assert math.isclose(row['eligible_passes_per90'], row['eligible_completed_passes'] / row['minutes'] * 90)
    if row['eligible_completed_passes']:
        assert math.isclose(row['qualifying_share_pct'], row['qualifying_passes'] / row['eligible_completed_passes'] * 100)
        assert math.isclose(row['qualifying_per90'], row['eligible_passes_per90'] * row['qualifying_share_pct'] / 100)
    else:
        assert row['qualifying_share_pct'] is None

# Check a genuinely held-out match split and recompute saved model predictions/scores.
train_ids, test_ids = set(model['training_match_ids']), set(model['test_match_ids'])
assert len(train_ids) == 5 and len(test_ids) == 2 and train_ids.isdisjoint(test_ids)
assert train_ids | test_ids == set(base['match_ids'])
train = [r for r in model['shots'] if r['split'] == 'train']
test = [r for r in model['shots'] if r['split'] == 'test']
assert len(train) == model['training_shots'] == 114
assert len(test) == model['test_shots'] == 36
assert sum(r['goal'] for r in train) == model['training_goals'] == 11
assert sum(r['goal'] for r in test) == model['test_goals'] == 6
assert all(r['match_id'] in train_ids for r in train)
assert all(r['match_id'] in test_ids for r in test)
ids(model['shots'])
mean_distance = sum(r['distance'] for r in train) / len(train)
scale = math.sqrt(sum((r['distance'] - mean_distance) ** 2 for r in train) / len(train))
assert math.isclose(model['training_mean_distance'], mean_distance)
assert math.isclose(model['training_scale_distance'], scale)
assert math.isclose(model['baseline_training_goal_rate'], 11 / 114)
assert model['optimisation_success']
for row in model['shots']:
    assert row['goal'] in [0, 1]
    assert math.isclose(row['distance'], math.hypot(120 - row['x'], 40 - row['y']))
    z = model['intercept_scaled'] + model['distance_coefficient_scaled'] * (row['distance'] - mean_distance) / scale
    predicted = 1 / (1 + math.exp(-z))
    assert 0 < row['predicted_xg'] < 1 and math.isclose(row['predicted_xg'], predicted)
for key, probabilities in [
        ('model_test_metrics', [r['predicted_xg'] for r in test]),
        ('baseline_test_metrics', [11 / 114] * len(test))]:
    brier = sum((p - r['goal']) ** 2 for p, r in zip(probabilities, test)) / len(test)
    log_loss = -sum(r['goal'] * math.log(p) + (1 - r['goal']) * math.log(1 - p)
                    for p, r in zip(probabilities, test)) / len(test)
    assert math.isclose(model[key]['brier_score'], brier)
    assert math.isclose(model[key]['log_loss'], log_loss)
    assert math.isclose(model[key]['predicted_goal_total'], sum(probabilities))

# Lesson 19: reconcile every time window, not only headline totals.
window_study = read('19_time_window_evidence.json')
assert window_study['windows_seconds_inclusive'] == [5, 10, 15]
assert window_study['xg_threshold_strictly_greater_than'] == 0.10
previous_ids = set()
for window, expected_total in [(5, 38), (10, 68), (15, 98)]:
    result = window_study['windows'][str(window)]
    expected_rows = [p for p in high if 0 <= p['seconds_before_shot'] <= window]
    assert result['selected_passes'] == expected_rows
    current_ids = ids(result['selected_passes'])
    assert previous_ids <= current_ids
    previous_ids = current_ids
    assert result['total'] == len(current_ids) == expected_total
    by_player = Counter(p['player_id'] for p in expected_rows)
    assert len(result['players']) == len(sensitivity['players'])
    assert len({p['player_id'] for p in result['players']}) == len(result['players'])
    original_players = {p['player_id']: p for p in sensitivity['players']}
    for player in result['players']:
        original = original_players[player['player_id']]
        assert player['player_name'] == original['player_name']
        assert player['minutes'] == original['minutes']
        assert player['count'] == by_player[player['player_id']]
        assert math.isclose(player['per90'], player['count'] / player['minutes'] * 90)
    assert sum(p['count'] for p in result['players']) == result['total']
assert previous_ids == ids(high)

# Independently reconstruct from raw events when available. This verifies that
# filtering the saved nearest-shot gaps gives the full shorter-window selections.
raw_window_matches = 0
for match_id in base['match_ids']:
    path = ROOT / f'data/cache_2019_events/{match_id}.json'
    if not path.exists():
        continue
    events = json.loads(path.read_text())
    team_events = [e for e in events if e['team']['name'] == "England Women's"]
    shots = [e for e in team_events if e['type']['name'] == 'Shot' and e['shot']['statsbomb_xg'] > 0.10]
    passes = [e for e in team_events if e['type']['name'] == 'Pass'
              and 'outcome' not in e['pass']
              and e['possession_team']['id'] == e['team']['id']
              and e['pass'].get('type', {}).get('name') not in
              ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']]
    for window in [5, 10, 15]:
        expected = set()
        for event in passes:
            if any(shot['period'] == event['period'] and shot['possession'] == event['possession']
                   and shot['index'] > event['index']
                   and 0 <= (shot['minute'] - event['minute']) * 60 + shot['second'] - event['second'] <= window
                   for shot in shots):
                expected.add((match_id, event['id']))
        saved = [p for p in window_study['windows'][str(window)]['selected_passes'] if p['match_id'] == match_id]
        assert ids(saved) == expected, f'Raw window reconstruction differs: {match_id}, {window}'
    raw_window_matches += 1

assert {p['match_id'] for p in manifest['raw_inputs']} == set(base['match_ids'])
checked = 0
for record in manifest['raw_inputs']:
    path = ROOT / record['relative_path']
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'Raw input changed: ' + path.name
        checked += 1
print('PASS: passing evidence, time-window selections and educational xG metrics reconcile.')
print(f'Time-window selections independently reconstructed from raw events: {raw_window_matches}/7 matches.')
print(f'Raw input hashes checked locally: {checked}/7 (cache is optional and not committed).')
