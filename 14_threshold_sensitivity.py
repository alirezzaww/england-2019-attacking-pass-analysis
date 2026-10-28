# Sensitivity analysis: does the result change when the shot-xG cutoff changes?
from pathlib import Path
from collections import Counter
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / 'data/13_minutes_and_quality_evidence.json').read_text())
players = pd.DataFrame(source['players'])[['player_id', 'player_name', 'minutes']].copy()
match_ids = sorted({p['match_id'] for p in source['all_qualifying_passes']})
shots_by_match, goalkeeper_ids = {}, set()
for match_id in match_ids:
    events = json.loads((ROOT / f'data/cache_2019_events/{match_id}.json').read_text())
    team = [e for e in events if e['team']['name'] == "England Women's"]
    shots_by_match[match_id] = [e for e in team if e['type']['name'] == 'Shot']
    for e in team:
        if e['type']['name'] == 'Starting XI':
            goalkeeper_ids.update(p['player']['id'] for p in e['tactics']['lineup'] if p['position']['id'] == 1)

selected = {}
for threshold, suffix in [(0.07, '007'), (0.10, '010')]:
    rows = []
    for p in source['all_qualifying_passes']:
        shots = [s for s in shots_by_match[p['match_id']]
                 if s['shot']['statsbomb_xg'] > threshold
                 and s['period'] == p['period'] and s['possession'] == p['possession']
                 and s['index'] > p['index']
                 and 0 <= s['minute'] * 60 + s['second'] - p['clock'] <= 15]
        if shots:
            s = min(shots, key=lambda e: (e['minute'] * 60 + e['second'] - p['clock'], e['index']))
            rows.append({**p, 'shot_id': s['id'], 'shot_xg': s['shot']['statsbomb_xg'],
                         'seconds_before_shot': s['minute'] * 60 + s['second'] - p['clock']})
    selected[f'{threshold:.2f}'] = rows
    counts = Counter(p['player_id'] for p in rows)
    players[f'count_{suffix}'] = players.player_id.map(counts).fillna(0).astype(int)
    players[f'per90_{suffix}'] = players[f'count_{suffix}'] / players.minutes * 90
    assert players[f'count_{suffix}'].sum() == len(rows)
    print(f'xG > {threshold:.2f}: {len(rows)} passes')
assert {p['id'] for p in selected['0.07']} == {p['id'] for p in source['passes_before_shots_above_threshold']}
assert {p['id'] for p in selected['0.10']}.issubset({p['id'] for p in selected['0.07']})
assert (players.count_010 <= players.count_007).all()
display = players[(players.minutes >= 270) & ~players.player_id.isin(goalkeeper_ids)].copy()
display = display.sort_values(['per90_010', 'player_name'], ascending=[True, False])
print(display.sort_values('per90_010', ascending=False).round(2).to_string(index=False))

fig, ax = plt.subplots(figsize=(13, 8))
fig.subplots_adjust(left=0.25, right=0.94, top=0.80, bottom=0.21)
y = np.arange(len(display))
for offset, suffix, color, label in [(0.18, '007', '#24658a', 'Shot xG > 0.07'),
                                      (-0.18, '010', '#b77516', 'Shot xG > 0.10')]:
    ax.barh(y + offset, display[f'per90_{suffix}'], height=0.32, color=color, label=label)
    for i, value in enumerate(display[f'per90_{suffix}']):
        ax.text(value + 0.04, i + offset, f'{value:.2f}', va='center', fontsize=10)
ax.set_yticks(y, [f'{r.player_name} ({r.minutes:.0f} min)' for r in display.itertuples()], fontsize=10)
ax.set_xlim(0, display.per90_007.max() + 0.6)
ax.set_xlabel('Qualifying passes per 90 reconstructed minutes', fontsize=11)
ax.grid(axis='x', color='#e4e7ea')
ax.set_axisbelow(True)
for side in ['top', 'right', 'left']:
    ax.spines[side].set_visible(False)
ax.legend(loc='lower right', frameon=False, fontsize=10)
fig.suptitle('England: does changing the xG cutoff change the comparison?', fontsize=18, weight='bold', y=0.96)
fig.text(0.5, 0.875, '2019 Women’s World Cup · 9 June–6 July · Seven games\nSame passes, timing rules and playing-time method · Outfield players with 270+ reconstructed minutes', ha='center', fontsize=11)
fig.text(0.5, 0.055,
         'Filter shots first, then match and count each qualifying pass once · xG belongs to the following shot\n'
         'Minutes include added time; halftime excluded; temporary injury absences retained · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
fig.savefig(ROOT / 'figures/17_england_xg_threshold_sensitivity.png', dpi=180, bbox_inches='tight')
evidence = {'thresholds': [0.07, 0.10], 'players': players.to_dict(orient='records'),
            'selected_passes': selected, 'minimum_display_minutes': 270,
            'minutes_method_source': '13_minutes_and_quality_evidence.json'}
(ROOT / 'data/14_threshold_sensitivity_evidence.json').write_text(json.dumps(evidence, indent=2))
plt.show()
