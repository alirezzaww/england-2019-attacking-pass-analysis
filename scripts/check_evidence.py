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

# Lesson 20: denominator and numerator must come from the same starting third.
context = read('20_pass_location_evidence.json')
zone_names = ['Defensive third', 'Middle third', 'Attacking third']
assert context['match_ids'] == base['match_ids']
assert context['windows_seconds_inclusive'] == 15
assert context['xg_threshold_strictly_greater_than'] == 0.10
assert context['zones'] == [
    {'name': name, 'lower_x_inclusive': low, 'upper_x': upper, 'upper_inclusive': upper == 120}
    for name, low, upper in zip(zone_names, [0, 40, 80], [40, 80, 120])]
ledger = context['passes']
assert len(ledger) == len(ids(ledger)) == context['eligible_completed_passes'] == volume['eligible_passes_total']
assert ids([p for p in ledger if p['qualifying']]) == ids(high)
assert context['qualifying_passes'] == len(high)
assert all(type(p['qualifying']) is bool for p in ledger)
assert all(p['match_id'] in base['match_ids'] for p in ledger)
for row in ledger:
    assert math.isfinite(row['x']) and 0 <= row['x'] <= 120
    assert row['zone'] == zone_names[min(int(row['x'] // 40), 2)]
zone_denominators = Counter((p['player_id'], p['zone']) for p in ledger)
zone_numerators = Counter((p['player_id'], p['zone']) for p in ledger if p['qualifying'])
assert len({p['player_id'] for p in context['players']}) == len(context['players'])
original_players = {p['player_id']: p for p in volume['players']}
assert {p['player_id'] for p in context['players']} == set(original_players)
assert {p['player_id'] for p in ledger} <= set(original_players)
for player in context['players']:
    original = original_players[player['player_id']]
    assert player['player_name'] == original['player_name']
    assert player['eligible_completed_passes'] == original['eligible_completed_passes']
    assert player['qualifying_passes'] == original['qualifying_passes']
    assert [row['zone'] for row in player['zones']] == zone_names
    total = player['eligible_completed_passes']
    assert sum(r['eligible_completed_passes'] for r in player['zones']) == total
    assert sum(r['qualifying_passes'] for r in player['zones']) == player['qualifying_passes']
    overall = player['overall_qualifying_share_pct']
    if total:
        assert math.isclose(overall, player['qualifying_passes'] / total * 100)
        assert math.isclose(sum(r['pass_start_mix_pct'] for r in player['zones']), 100)
    else:
        assert overall is None
    for row in player['zones']:
        key = (player['player_id'], row['zone'])
        n, k = zone_denominators[key], zone_numerators[key]
        assert row['eligible_completed_passes'] == n and row['qualifying_passes'] == k
        assert 0 <= k <= n
        if n:
            assert math.isclose(row['qualifying_share_pct'], k / n * 100)
        else:
            assert row['qualifying_share_pct'] is None
        if total:
            assert math.isclose(row['pass_start_mix_pct'], n / total * 100)
        else:
            assert row['pass_start_mix_pct'] is None

raw_context_matches = 0
for match_id in base['match_ids']:
    path = ROOT / f'data/cache_2019_events/{match_id}.json'
    if not path.exists():
        continue
    expected = {}
    for event in json.loads(path.read_text()):
        if (event['type']['name'] == 'Pass' and event['team']['name'] == "England Women's"
                and 'outcome' not in event['pass']
                and event['possession_team']['id'] == event['team']['id']
                and event['pass'].get('type', {}).get('name') not in
                ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']):
            expected[event['id']] = (event['player']['id'], event['location'][0])
    actual = {p['id']: (p['player_id'], p['x']) for p in ledger if p['match_id'] == match_id}
    assert actual == expected, f'Pass-location denominator differs from raw input: {match_id}'
    raw_context_matches += 1

# Lesson 21: rebuild fixture counts and replay every paired match draw offline.
bootstrap = read('21_match_bootstrap_evidence.json')
assert bootstrap['source'] == '20_pass_location_evidence.json'
assert bootstrap['zone'] == 'Attacking third'
assert bootstrap['xg_threshold_strictly_greater_than'] == 0.10
assert bootstrap['time_window_seconds_inclusive'] == 15
assert [p['player_name'] for p in bootstrap['player_order']] == ['Francesca Kirby', 'Lucy Bronze']
expected_players = [next(p for p in context['players'] if p['player_name'] == name)
                    for name in ['Francesca Kirby', 'Lucy Bronze']]
assert bootstrap['player_order'] == [{'player_id': p['player_id'], 'player_name': p['player_name']} for p in expected_players]
fixture_rows = []
for match_id in base['match_ids']:
    cells = []
    for player in bootstrap['player_order']:
        passes = [p for p in ledger if p['match_id'] == match_id and p['player_id'] == player['player_id'] and p['x'] >= 80]
        cells.append({'qualifying_passes': sum(p['qualifying'] for p in passes), 'eligible_completed_passes': len(passes)})
    fixture_rows.append({'match_id': match_id, 'players': cells})
assert bootstrap['match_counts'] == fixture_rows
for j, expected_share in enumerate(bootstrap['observed_shares_pct']):
    k = sum(row['players'][j]['qualifying_passes'] for row in fixture_rows)
    n = sum(row['players'][j]['eligible_completed_passes'] for row in fixture_rows)
    assert math.isclose(expected_share, 100 * k / n)
assert math.isclose(bootstrap['observed_difference_percentage_points'], bootstrap['observed_shares_pct'][0] - bootstrap['observed_shares_pct'][1])
import random
rng = random.Random(bootstrap['seed'])
assert bootstrap['n_resamples'] == 10000 and bootstrap['seed'] == 20261030
replayed, invalid = [], 0
for draw in range(bootstrap['n_resamples']):
    indices = [rng.randrange(len(fixture_rows)) for _ in fixture_rows]
    if draw == 0:
        assert bootstrap['example_match_ids'] == [fixture_rows[i]['match_id'] for i in indices]
    totals = [[sum(fixture_rows[i]['players'][j][key] for i in indices)
               for key in ['qualifying_passes', 'eligible_completed_passes']] for j in range(2)]
    if any(n == 0 for k, n in totals):
        invalid += 1
    else:
        replayed.append(100 * totals[0][0] / totals[0][1] - 100 * totals[1][0] / totals[1][1])
assert bootstrap['valid_resamples'] == len(replayed)
assert bootstrap['zero_denominator_resamples'] == invalid
assert len(replayed) + invalid == bootstrap['n_resamples']
assert bootstrap['differences_percentage_points'] == replayed
assert bootstrap['percentiles'] == [0.025, 0.975]
assert bootstrap['percentile_method'] == 'linear interpolation at (n - 1) * q'
ordered = sorted(replayed)
for quantile, endpoint in zip(bootstrap['percentiles'], bootstrap['illustrative_interval_percentage_points']):
    position = quantile * (len(ordered) - 1)
    fraction = position % 1
    expected = (1 - fraction) * ordered[math.floor(position)] + fraction * ordered[math.ceil(position)]
    assert math.isclose(expected, endpoint)

# Lesson 22: use the score before each pass, not the final result or future goals.
score_context = read('22_score_state_evidence.json')
assert score_context['match_ids'] == base['match_ids']
assert score_context['time_window_seconds_inclusive'] == 15
assert score_context['xg_threshold_strictly_greater_than'] == 0.10
state_ledger = score_context['passes']
assert ids(state_ledger) == ids(ledger)
original_passes = {(p['match_id'], p['id']): p for p in ledger}
state_names = ['Leading', 'Drawing', 'Trailing']
audit_by_match = {a['match_id']: a for a in score_context['match_audits']}
assert len(audit_by_match) == len(score_context['match_audits']) == 7
assert set(audit_by_match) == set(base['match_ids'])

def check_state_summary(saved, passes):
    assert [r['state'] for r in saved] == state_names
    for row in saved:
        group = [p for p in passes if p['state'] == row['state']]
        k, n = sum(p['qualifying'] for p in group), len(group)
        assert row['eligible_completed_passes'] == n and row['qualifying_passes'] == k
        if n:
            assert math.isclose(row['qualifying_share_pct'], 100 * k / n)
        else:
            assert row['qualifying_share_pct'] is None

for match_id, audit in audit_by_match.items():
    tally = [0, 0]
    last_index = -1
    for goal in audit['goals']:
        assert goal['index'] > last_index
        assert goal['score_before'] == tally
        credited = goal['credited_team_id']
        assert credited in [audit['england_team_id'], audit['opponent_team_id']]
        tally[0 if credited == audit['england_team_id'] else 1] += 1
        assert goal['score_after'] == tally
        last_index = goal['index']
    assert tally == audit['provider_final_score_england_opponent'] == audit['reconstructed_final_score_england_opponent']
    rows = [p for p in state_ledger if p['match_id'] == match_id]
    for row in rows:
        original = original_passes[(match_id, row['id'])]
        assert row['player_id'] == original['player_id'] and row['qualifying'] == original['qualifying']
        prior = [g for g in audit['goals'] if g['index'] < row['index']]
        before = prior[-1]['score_after'] if prior else [0, 0]
        assert [row['england_goals_before'], row['opponent_goals_before']] == before
        expected_state = 'Leading' if before[0] > before[1] else 'Trailing' if before[0] < before[1] else 'Drawing'
        assert row['state'] == expected_state
    check_state_summary(audit['states'], rows)
check_state_summary(score_context['team_states'], state_ledger)
assert sum(r['qualifying_passes'] for r in score_context['team_states']) == 98
assert sum(r['eligible_completed_passes'] for r in score_context['team_states']) == 2837
assert {p['match_id'] for p in state_ledger if p['state'] == 'Trailing'} == {69258, 69301}
assert {p['player_id'] for p in score_context['players']} == set(original_players)
assert len(score_context['players']) == len(original_players)
for player in score_context['players']:
    assert player['player_name'] == original_players[player['player_id']]['player_name']
    check_state_summary(player['states'], [p for p in state_ledger if p['player_id'] == player['player_id']])
metadata_source = score_context['metadata_source']
assert metadata_source['url'] == 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/72/30.json'
metadata_path = ROOT / metadata_source['relative_path']
if metadata_path.exists():
    assert hashlib.sha256(metadata_path.read_bytes()).hexdigest() == metadata_source['sha256']
    metadata = {m['match_id']: m for m in json.loads(metadata_path.read_text())}
    for match_id, audit in audit_by_match.items():
        match = metadata[match_id]
        home = match['home_team']['home_team_name'] == "England Women's"
        expected = [match['home_score'], match['away_score']] if home else [match['away_score'], match['home_score']]
        assert expected == audit['provider_final_score_england_opponent']

raw_score_matches = 0
for match_id, audit in audit_by_match.items():
    path = ROOT / f'data/cache_2019_events/{match_id}.json'
    if not path.exists():
        continue
    rows = {p['id']: p for p in state_ledger if p['match_id'] == match_id}
    tally = [0, 0]
    raw_goal_ids = []
    for event in sorted(json.loads(path.read_text()), key=lambda e: e['index']):
        if event['period'] == 5:
            continue
        if event['id'] in rows:
            saved = rows[event['id']]
            assert saved['index'] == event['index']
            assert [saved['england_goals_before'], saved['opponent_goals_before']] == tally
        kind = event['type']['name']
        if kind == 'Shot' and event['shot']['outcome']['name'] == 'Goal':
            tally[0 if event['team']['id'] == audit['england_team_id'] else 1] += 1
            raw_goal_ids.append(event['id'])
        elif kind == 'Own Goal Against':
            tally[1 if event['team']['id'] == audit['england_team_id'] else 0] += 1
            raw_goal_ids.append(event['id'])
    assert raw_goal_ids == [g['id'] for g in audit['goals']]
    assert tally == audit['provider_final_score_england_opponent']
    raw_score_matches += 1

# Lesson 23: a within-match comparison needs observations in both states.
within = read('23_within_match_evidence.json')
assert within['source'] == '22_score_state_evidence.json'
assert within['match_ids'] == base['match_ids']
assert within['time_window_seconds_inclusive'] == 15
assert within['xg_threshold_strictly_greater_than'] == 0.10
assert [m['match_id'] for m in within['coverage']] == base['match_ids']
for match in within['coverage']:
    assert match['opponent'] == audit_by_match[match['match_id']]['opponent']
    check_state_summary(match['states'], [p for p in state_ledger if p['match_id'] == match['match_id']])
assert set(within['comparisons']) == {'drawing_vs_trailing', 'leading_vs_trailing'}
for name, comparison in within['comparisons'].items():
    first, second = comparison['states']
    assert name == f'{first.lower()}_vs_{second.lower()}'
    observed = {state: {p['match_id'] for p in state_ledger if p['state'] == state} for state in [first, second]}
    expected_common = [m for m in base['match_ids'] if m in observed[first] & observed[second]]
    assert comparison['common_match_ids'] == expected_common
    for key, rows in [('all_fixture_pool', state_ledger),
                      ('common_fixture_pool', [p for p in state_ledger if p['match_id'] in expected_common])]:
        assert [c['state'] for c in comparison[key]] == [first, second]
        for cell in comparison[key]:
            group = [p for p in rows if p['state'] == cell['state']]
            k, n = sum(p['qualifying'] for p in group), len(group)
            assert cell['qualifying_passes'] == k and cell['eligible_completed_passes'] == n
            if n:
                assert math.isclose(cell['qualifying_share_pct'], 100 * k / n)
            else:
                assert cell['qualifying_share_pct'] is None
        shares = [c['qualifying_share_pct'] for c in comparison[key]]
        difference_key = ('all' if key == 'all_fixture_pool' else 'common') + '_difference_second_minus_first_pp'
        if any(value is None for value in shares):
            assert comparison[difference_key] is None
        else:
            assert math.isclose(comparison[difference_key], shares[1] - shares[0], abs_tol=1e-12)
    assert [row['match_id'] for row in comparison['per_common_fixture']] == expected_common
    for fixture in comparison['per_common_fixture']:
        original = {r['state']: r for r in audit_by_match[fixture['match_id']]['states']}
        assert fixture['states'] == [original[state] for state in [first, second]]
assert within['comparisons']['leading_vs_trailing']['common_match_ids'] == []
assert within['comparisons']['drawing_vs_trailing']['common_match_ids'] == [69258, 69301]

# Lesson 24: pass rows, represented shots and possessions are distinct units.
units = read('24_shot_units_evidence.json')
assert units['sources'] == ['14_threshold_sensitivity_evidence.json', '22_score_state_evidence.json']
assert units['time_window_seconds_inclusive'] == 15 and units['xg_threshold_strictly_greater_than'] == 0.10
expected_ids = ids([p for p in state_ledger if p['state'] == 'Trailing' and p['qualifying']])
expected_passes = [p for p in high if (p['match_id'], p['id']) in expected_ids]
flattened = [p for group in units['groups'] for p in group['selected_passes']]
assert ids(flattened) == expected_ids
assert {(p['match_id'], p['id']): p for p in flattened} == {(p['match_id'], p['id']): p for p in expected_passes}
shot_keys = {(p['match_id'], p['shot_id']) for p in expected_passes}
assert {(g['match_id'], g['shot']['id']) for g in units['groups']} == shot_keys
assert len(units['groups']) == len(shot_keys)
for group in units['groups']:
    shot = group['shot']
    rows = group['selected_passes']
    assert group['opponent'] == audit_by_match[group['match_id']]['opponent']
    assert rows == sorted(rows, key=lambda p: p['index'])
    for row in rows:
        assert row['match_id'] == group['match_id'] and row['shot_id'] == shot['id']
        assert row['shot_xg'] == shot['xg'] > 0.10
        assert row['possession'] == shot['possession'] and row['period'] == shot['period']
        assert row['index'] < shot['index']
        assert shot['minute'] * 60 + shot['second'] - row['clock'] == row['seconds_before_shot']
    prior = [g for g in audit_by_match[group['match_id']]['goals'] if g['index'] < shot['index']]
    assert shot['score_before_england_opponent'] == (prior[-1]['score_after'] if prior else [0, 0])
    path = ROOT / f"data/cache_2019_events/{group['match_id']}.json"
    if path.exists():
        original = next(e for e in json.loads(path.read_text()) if e['id'] == shot['id'])
        assert original['type']['name'] == 'Shot' and original['team']['name'] == "England Women's"
        for key in ['index', 'period', 'possession', 'minute', 'second']:
            assert shot[key] == original[key]
        assert shot['player_name'] == original['player']['name']
        assert shot['xg'] == original['shot']['statsbomb_xg']
        assert shot['outcome'] == original['shot']['outcome']['name']
summary = units['summary']
assert summary['qualifying_passes'] == len(expected_passes) == 12
assert summary['distinct_assigned_shots'] == len(shot_keys) == 3
assert summary['distinct_possessions'] == len({(p['match_id'], p['period'], p['possession']) for p in expected_passes}) == 3
assert summary['goals_from_represented_shots'] == sum(g['shot']['outcome'] == 'Goal' for g in units['groups']) == 2
unique_xg = sum(g['shot']['xg'] for g in units['groups'])
repeated_xg = sum(p['shot_xg'] for p in expected_passes)
assert math.isclose(summary['assigned_shot_xg_counted_once'], unique_xg)
assert math.isclose(summary['incorrect_repeated_shot_xg_sum_for_demonstration'], repeated_xg)

# Lesson 25: geometry, grouped training-only validation and fold-local scaling.
angle_study = read('25_shot_angle_evidence.json')
assert angle_study['source'] == '18_first_xg_model_evidence.json'
assert angle_study['training_match_ids'] == model['training_match_ids']
assert angle_study['reused_test_match_ids'] == model['test_match_ids']
assert set(angle_study['training_match_ids']).isdisjoint(angle_study['reused_test_match_ids'])
assert angle_study['primary_selection_metric'] == 'pooled training-only leave-one-match-out log loss'
angle_rows = angle_study['shots']
assert ids(angle_rows) == ids(model['shots'])
source_shots = {(r['match_id'], r['id']): r for r in model['shots']}
for row in angle_rows:
    original = source_shots[(row['match_id'], row['id'])]
    for key in ['x', 'y', 'goal', 'split', 'body_part']:
        assert row[key] == original[key]
    dx, lateral = (120 - row['x']) * 105 / 120, (row['y'] - 40) * 68 / 80
    # Independent angle check from the dot product of vectors to each goalpost.
    a, b = -3.66 - lateral, 3.66 - lateral
    cosine = (dx * dx + a * b) / (math.hypot(dx, a) * math.hypot(dx, b))
    expected_angle = math.acos(max(-1, min(1, cosine)))
    assert math.isclose(row['distance_template_m'], math.hypot(dx, lateral))
    assert math.isclose(row['angle_radians'], expected_angle, abs_tol=1e-10)
angle_train = [r for r in angle_rows if r['split'] == 'train']
angle_test = [r for r in angle_rows if r['split'] == 'test']
assert len(angle_train) == 114 and len(angle_test) == 36
expected_features = {'constant': [], 'distance': ['distance_template_m'],
                     'distance_angle': ['distance_template_m', 'angle_radians']}
assert set(angle_study['candidates']) == set(expected_features)

def angle_prediction(fit, row):
    z = fit['coefficients'][0] + sum(fit['coefficients'][j + 1] * (row[f] - fit['means'][j]) / fit['scales'][j]
                                    for j, f in enumerate(fit['features']))
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    exponent = math.exp(z)
    return exponent / (1 + exponent)

def check_angle_fit(fit, fitting_rows, features):
    assert fit['features'] == features and fit['converged']
    assert len(fit['coefficients']) == len(features) + 1
    assert len(fit['means']) == len(fit['scales']) == len(features)
    assert all(math.isfinite(v) for v in fit['coefficients'])
    for j, f in enumerate(features):
        mean = sum(r[f] for r in fitting_rows) / len(fitting_rows)
        scale = math.sqrt(sum((r[f] - mean) ** 2 for r in fitting_rows) / len(fitting_rows))
        assert math.isclose(fit['means'][j], mean)
        assert scale > 0 and math.isclose(fit['scales'][j], scale)
    predictions = [angle_prediction(fit, r) for r in fitting_rows]
    if not features:
        rate = sum(r['goal'] for r in fitting_rows) / len(fitting_rows)
        assert all(math.isclose(p, rate) for p in predictions)
    # Check the stored fit satisfies the logistic likelihood gradient tolerance.
    residuals = [p - r['goal'] for p, r in zip(predictions, fitting_rows)]
    assert abs(sum(residuals) / len(residuals)) < 1e-5
    for j, f in enumerate(features):
        gradient = sum(error * (r[f] - fit['means'][j]) / fit['scales'][j]
                       for error, r in zip(residuals, fitting_rows)) / len(fitting_rows)
        assert abs(gradient) < 1e-5

def check_angle_scores(saved, rows, predictions):
    assert len(rows) == len(predictions) and rows
    assert all(math.isfinite(p) and 0 <= p <= 1 for p in predictions)
    brier = sum((p - r['goal']) ** 2 for p, r in zip(predictions, rows)) / len(rows)
    clipped = [max(1e-12, min(1 - 1e-12, p)) for p in predictions]
    loss = -sum(r['goal'] * math.log(p) + (1 - r['goal']) * math.log(1 - p)
                for r, p in zip(rows, clipped)) / len(rows)
    assert math.isclose(saved['brier_score'], brier)
    assert math.isclose(saved['log_loss'], loss)
    assert math.isclose(saved['predicted_goal_total'], sum(predictions))

for name, candidate in angle_study['candidates'].items():
    features = expected_features[name]
    assert candidate['features'] == features
    folds = candidate['validation_folds']
    assert [f['validation_match_id'] for f in folds] == angle_study['training_match_ids']
    validation_rows, validation_predictions = [], []
    for fold in folds:
        held_id = fold['validation_match_id']
        expected_fit_ids = [m for m in angle_study['training_match_ids'] if m != held_id]
        assert fold['fitting_match_ids'] == expected_fit_ids
        assert held_id not in expected_fit_ids
        fitting = [r for r in angle_train if r['match_id'] in expected_fit_ids]
        held = [r for r in angle_train if r['match_id'] == held_id]
        assert fold['validation_shot_ids'] == [r['id'] for r in held]
        check_angle_fit(fold['fit'], fitting, features)
        assert len(fold['predictions']) == len(held)
        assert all(math.isclose(p, angle_prediction(fold['fit'], r)) for p, r in zip(fold['predictions'], held))
        validation_rows.extend(held); validation_predictions.extend(fold['predictions'])
    assert ids(validation_rows) == ids(angle_train)
    check_angle_scores(candidate['validation_metrics'], validation_rows, validation_predictions)
    check_angle_fit(candidate['fit_all_training'], angle_train, features)
    assert candidate['reused_test_shot_ids'] == [r['id'] for r in angle_test]
    assert len(candidate['reused_test_predictions']) == len(angle_test)
    assert all(math.isclose(p, angle_prediction(candidate['fit_all_training'], r))
               for p, r in zip(candidate['reused_test_predictions'], angle_test))
    check_angle_scores(candidate['reused_test_metrics'], angle_test, candidate['reused_test_predictions'])
winner = min(angle_study['candidates'], key=lambda n: angle_study['candidates'][n]['validation_metrics']['log_loss'])
assert angle_study['selected_candidate'] == winner

assert {p['match_id'] for p in manifest['raw_inputs']} == set(base['match_ids'])
checked = 0
for record in manifest['raw_inputs']:
    path = ROOT / record['relative_path']
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'Raw input changed: ' + path.name
        checked += 1
print('PASS: passing evidence, shot units, match context, bootstrap and both xG studies reconcile.')
print(f'Pre-pass scores independently reconstructed from raw events: {raw_score_matches}/7 matches.')
print(f'Location denominators independently reconstructed from raw events: {raw_context_matches}/7 matches.')
print(f'Time-window selections independently reconstructed from raw events: {raw_window_matches}/7 matches.')
print(f'Raw input hashes checked locally: {checked}/7 (cache is optional and not committed).')
