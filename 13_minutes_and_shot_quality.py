# Faster lesson block: playing time, per-90 rates, and the course's xG > 0.07 challenge.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
import json
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
TEAM = "England Women's"
XG_THRESHOLD = 0.07
MIN_MINUTES = 270  # transparent teaching display rule, not a statistical guarantee
base = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
CACHE = ROOT / 'data/cache_2019_events'
CACHE.mkdir(exist_ok=True)

def seconds(timestamp):
    hours, minutes, secs = map(float, timestamp.split(':'))
    return hours * 3600 + minutes * 60 + secs

def select_passes(passes, shots):
    """Select each pass once, against the next qualifying shot in its possession."""
    selected = []
    for event in passes:
        candidates = [shot for shot in shots
                      if shot['period'] == event['period']
                      and shot['possession'] == event['possession']
                      and shot['index'] > event['index']
                      and 0 <= shot['clock'] - event['clock'] <= 15]
        if candidates:
            shot = min(candidates, key=lambda row: (row['clock'] - event['clock'], row['index']))
            selected.append({**event, 'shot_id': shot['id'], 'shot_xg': shot['xg'],
                             'seconds_before_shot': shot['clock'] - event['clock']})
    return selected

intervals, audits, all_passes, high_passes = [], [], [], []
goalkeepers = set()
for match_id in base['match_ids']:
    path = CACHE / f'{match_id}.json'
    if not path.exists():
        response = requests.get(f'https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json', timeout=60)
        response.raise_for_status()
        path.write_text(json.dumps(response.json()))
    events = json.loads(path.read_text())
    # Reconstruct elapsed playing time across halves; exclude the halftime interval.
    periods = sorted({e['period'] for e in events if e['period'] < 5})
    lengths = {p: max(seconds(e['timestamp']) for e in events
                      if e['period'] == p and e['type']['name'] == 'Half End') for p in periods}
    offsets = {p: sum(lengths[q] for q in periods if q < p) for p in periods}
    match_end = sum(lengths.values())
    elapsed = lambda e: offsets[e['period']] + seconds(e['timestamp'])
    team = [e for e in events if e['team']['name'] == TEAM and e['period'] < 5]
    start = next(e for e in team if e['type']['name'] == 'Starting XI')
    lineup = start['tactics']['lineup']
    assert len(lineup) == 11
    active = {p['player']['id']: (0.0, p['player']['name']) for p in lineup}
    goalkeepers.update(p['player']['id'] for p in lineup if p['position']['id'] == 1)
    match_intervals = []
    lost_seconds = 0.0
    temporary_off_events = []

    def close_interval(player_id, end, reason):
        began, name = active.pop(player_id)
        assert end >= began
        match_intervals.append({'match_id': match_id, 'player_id': player_id,
                                'player_name': name, 'start_seconds': began,
                                'end_seconds': end, 'end_reason': reason,
                                'minutes': (end - began) / 60})

    for e in sorted(team, key=lambda row: row['index']):
        kind = e['type']['name']
        card = e.get('foul_committed', {}).get('card', e.get('bad_behaviour', {}).get('card', {})).get('name')
        if kind == 'Substitution':
            close_interval(e['player']['id'], elapsed(e), 'Substitution')
            replacement = e['substitution']['replacement']
            assert replacement['id'] not in active
            active[replacement['id']] = (elapsed(e), replacement['name'])
        elif card in ['Red Card', 'Second Yellow'] or (
                kind == 'Player Off' and e.get('player_off', {}).get('permanent', False)):
            close_interval(e['player']['id'], elapsed(e), card or 'Permanent departure')
            lost_seconds += match_end - elapsed(e)
        elif kind in ['Player Off', 'Player On']:
            # Registered playing time convention: retain temporary injury absences.
            temporary_off_events.append({'id': e['id'], 'type': kind, 'player': e['player']['name']})
    for player_id in list(active):
        close_interval(player_id, match_end, 'Full time')
    assert np.isclose(sum(r['minutes'] for r in match_intervals) * 60,
                      11 * match_end - lost_seconds)
    intervals.extend(match_intervals)
    audits.append({'match_id': match_id, 'period_seconds': lengths,
                   'match_minutes': match_end / 60, 'temporary_absences_retained': temporary_off_events,
                   'sending_off_or_permanent_departure_seconds_lost': lost_seconds})

    passes, shots = [], []
    for e in team:
        common = {'match_id': match_id, 'id': e['id'], 'index': e['index'],
                  'period': e['period'], 'possession': e['possession'],
                  'clock': e['minute'] * 60 + e['second']}
        if e['type']['name'] == 'Shot':
            shots.append({**common, 'xg': e['shot']['statsbomb_xg']})
        if (e['type']['name'] == 'Pass' and 'outcome' not in e['pass']
                and e['possession_team']['id'] == e['team']['id']
                and e['pass'].get('type', {}).get('name') not in ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']):
            player_id = e['player']['id']
            assert any(r['player_id'] == player_id and r['start_seconds'] <= elapsed(e) <= r['end_seconds']
                       for r in match_intervals)
            passes.append({**common, 'player_id': player_id, 'player_name': e['player']['name'],
                           'x': e['location'][0], 'y': e['location'][1]})
    all_passes.extend(select_passes(passes, shots))
    # Filter SHOTS first; then select/deduplicate passes. A later high-xG shot can qualify.
    high_passes.extend(select_passes(passes, [s for s in shots if s['xg'] > XG_THRESHOLD]))

assert {r['id'] for r in all_passes} == {r['id'] for r in base['selected_passes']}
assert {r['id'] for r in high_passes}.issubset({r['id'] for r in all_passes})
assert len({r['id'] for r in high_passes}) == len(high_passes)
assert all(r['shot_xg'] > XG_THRESHOLD for r in high_passes)
minutes = pd.DataFrame(intervals).groupby(['player_id', 'player_name'])['minutes'].sum().reset_index()
for label, rows in [('all_qualifying', all_passes), ('before_xg_above_007', high_passes)]:
    counts = pd.DataFrame(rows).groupby('player_id').size()
    minutes[label] = minutes.player_id.map(counts).fillna(0).astype(int)
    minutes[label + '_per90'] = minutes[label] / minutes.minutes * 90
assert minutes.all_qualifying.sum() == len(all_passes)
assert minutes.before_xg_above_007.sum() == len(high_passes)
assert minutes.minutes.gt(0).all()
print(minutes.sort_values('all_qualifying_per90', ascending=False).round(2).to_string(index=False))
print(f'\nAll qualifying passes: {len(all_passes)}; before xG > {XG_THRESHOLD}: {len(high_passes)}')

display = minutes[(minutes.minutes >= MIN_MINUTES) & ~minutes.player_id.isin(goalkeepers)]
display = display.sort_values(['all_qualifying_per90', 'player_name'], ascending=[True, False])
fig, ax = plt.subplots(figsize=(13, 8))
fig.subplots_adjust(left=0.25, right=0.94, top=0.80, bottom=0.22)
y = np.arange(len(display))
ax.barh(y + 0.18, display.all_qualifying_per90, height=0.32, color='#24658a', label='Before any shot')
ax.barh(y - 0.18, display.before_xg_above_007_per90, height=0.32, color='#b77516', label='Before a shot with xG > 0.07')
for i, row in enumerate(display.itertuples()):
    ax.text(row.all_qualifying_per90 + 0.06, i + 0.18, f'{row.all_qualifying_per90:.2f}', va='center', fontsize=10)
    ax.text(row.before_xg_above_007_per90 + 0.06, i - 0.18, f'{row.before_xg_above_007_per90:.2f}', va='center', fontsize=10)
ax.set_yticks(y, [f'{r.player_name} ({r.minutes:.0f} min)' for r in display.itertuples()], fontsize=10)
ax.set_xlim(0, display.all_qualifying_per90.max() + 0.8)
ax.set_xlabel('Qualifying passes per 90 reconstructed minutes', fontsize=11)
ax.grid(axis='x', color='#e4e7ea', zorder=0)
ax.set_axisbelow(True)
for side in ['top', 'right', 'left']:
    ax.spines[side].set_visible(False)
ax.legend(loc='lower right', frameon=False, fontsize=10)
fig.suptitle('England: playing time and the quality of the following shot', fontsize=19, weight='bold', y=0.96)
fig.text(0.5, 0.875, f"2019 Women's World Cup · 9 June–6 July · Seven matches\nOutfield players with {MIN_MINUTES}+ reconstructed minutes · 15-second, same-possession rule", ha='center', fontsize=11)
fig.text(0.5, 0.06,
         'Per 90 = pass count / minutes × 90 · Added time included; halftime excluded; temporary injury absences retained\n'
         'xG belongs to the following shot, not the pass · 0.07 is a course exercise threshold, not a universal high-quality cutoff\n'
         'Roles and opportunity still differ · Source: StatsBomb Open Data; Soccermatics', ha='center', fontsize=9)
figure = ROOT / 'figures/16_england_passes_per90_shot_quality.png'
fig.savefig(figure, dpi=180, bbox_inches='tight')
output = {'time_convention': 'Added time included, halftime excluded, temporary injury absences retained',
          'xg_threshold_strictly_greater_than': XG_THRESHOLD, 'minimum_display_minutes': MIN_MINUTES,
          'match_audits': audits, 'player_intervals': intervals,
          'players': minutes.to_dict(orient='records'), 'all_qualifying_passes': all_passes,
          'passes_before_shots_above_threshold': high_passes}
(ROOT / 'data/13_minutes_and_quality_evidence.json').write_text(json.dumps(output, indent=2))
print('Saved:', figure)
plt.show()
