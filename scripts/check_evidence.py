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

assert {p['match_id'] for p in manifest['raw_inputs']} == set(base['match_ids'])
checked = 0
for record in manifest['raw_inputs']:
    path = ROOT / record['relative_path']
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'Raw input changed: ' + path.name
        checked += 1
print('PASS: seven games; 200 passes; 113/98 threshold sets; minutes, rates, profile and match variation reconcile.')
print(f'Raw input hashes checked locally: {checked}/7 (cache is optional and not committed).')
