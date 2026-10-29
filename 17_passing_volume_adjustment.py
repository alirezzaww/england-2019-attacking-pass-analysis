# Project extension: per-90 frequency versus qualifying share of completed passes.
from pathlib import Path
from collections import Counter
import json
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())
base = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
selected = source['selected_passes']['0.10']
eligible_counts = Counter()
eligible_ids = set()
goalkeeper_ids = set()
for match_id in base['match_ids']:
    events = json.loads((ROOT / f'data/cache_2019_events/{match_id}.json').read_text())
    for event in events:
        if event['team']['name'] != "England Women's":
            continue
        if event['type']['name'] == 'Starting XI':
            goalkeeper_ids.update(p['player']['id'] for p in event['tactics']['lineup'] if p['position']['id'] == 1)
        if (event['type']['name'] == 'Pass' and 'outcome' not in event['pass']
                and event['possession_team']['id'] == event['team']['id']
                and event['pass'].get('type', {}).get('name') not in
                ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']):
            eligible_counts[event['player']['id']] += 1
            eligible_ids.add((match_id, event['id']))
assert {(p['match_id'], p['id']) for p in selected}.issubset(eligible_ids)
assert sum(eligible_counts.values()) == len(eligible_ids)
players = []
for player in source['players']:
    denominator = eligible_counts[player['player_id']]
    numerator = player['count_010']
    assert denominator >= numerator
    share = numerator / denominator * 100 if denominator else None
    volume = denominator / player['minutes'] * 90
    if denominator:
        # Same selected-pass rate decomposes into pass volume and qualifying share.
        assert np.isclose(player['per90_010'], volume * share / 100)
    players.append({'player_id': player['player_id'], 'player_name': player['player_name'],
                    'minutes': player['minutes'], 'qualifying_passes': numerator,
                    'qualifying_per90': player['per90_010'],
                    'eligible_completed_passes': denominator, 'eligible_passes_per90': volume,
                    'qualifying_share_pct': share})
assert sum(p['qualifying_passes'] for p in players) == len(selected) == 98
print(f'Eligible completed passes across seven games: {sum(eligible_counts.values())}')
for p in sorted(players, key=lambda row: row['qualifying_per90'], reverse=True):
    share_text = f'{p["qualifying_share_pct"]:.2f}%' if p['qualifying_share_pct'] is not None else 'undefined'
    print(f'{p["player_name"]}: {p["qualifying_passes"]} / {p["eligible_completed_passes"]} = '
          f'{share_text}; {p["qualifying_per90"]:.2f} qualifying per90')

display = [p for p in players if p['minutes'] >= 270 and p['player_id'] not in goalkeeper_ids]
display.sort(key=lambda p: (-p['qualifying_per90'], p['player_name']))
fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharey=True)
fig.subplots_adjust(left=0.22, right=0.97, top=0.79, bottom=0.22, wspace=0.18)
y = np.arange(len(display))
axes[0].barh(y, [p['qualifying_per90'] for p in display], color='#24658a', height=0.62)
axes[1].barh(y, [p['qualifying_share_pct'] for p in display], color='#b77516', height=0.62)
for i, p in enumerate(display):
    axes[0].text(p['qualifying_per90'] + 0.03, i, f'{p["qualifying_per90"]:.2f}', va='center', fontsize=10)
    axes[1].text(p['qualifying_share_pct'] + 0.10, i, f'{p["qualifying_share_pct"]:.2f}%', va='center', fontsize=10)
axes[0].set_yticks(y, [p['player_name'] for p in display], fontsize=10)
axes[0].invert_yaxis()
axes[0].set_xlim(0, max(p['qualifying_per90'] for p in display) + 0.5)
axes[1].set_xlim(0, max(p['qualifying_share_pct'] for p in display) + 1.5)
axes[0].set_title('Frequency relative to playing time', fontsize=12)
axes[1].set_title('Share of the player’s completed passes', fontsize=12)
axes[0].set_xlabel('Qualifying passes per 90 reconstructed minutes', fontsize=10)
axes[1].set_xlabel('Qualifying passes / eligible completed passes × 100 (%)', fontsize=10)
for ax in axes:
    ax.grid(axis='x', color='#e4e7ea')
    ax.set_axisbelow(True)
    for side in ['top', 'right', 'left']:
        ax.spines[side].set_visible(False)
fig.suptitle('England: changing the denominator changes the question', fontsize=20, weight='bold', y=0.96)
fig.text(0.5, 0.875,
         '2019 Women’s World Cup · Seven matches, 9 June–6 July\n'
         'Passes within 15 seconds before same-possession shots with xG > 0.10 · Outfield players with 270+ minutes',
         ha='center', fontsize=11)
fig.text(0.5, 0.055,
         'Denominator: possession-team completed passes, listed restarts excluded · This share is NOT pass completion rate\n'
         'Different axis units/scales · Does not control roles, pass difficulty or team possession · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures/20_england_passing_volume_adjustment.png'
fig.savefig(path, dpi=180, bbox_inches='tight')
output = {'xg_threshold_strictly_greater_than': 0.10, 'match_ids': base['match_ids'],
          'eligible_passes_total': sum(eligible_counts.values()), 'qualifying_passes_total': 98,
          'denominator_definition': 'Completed possession-team passes; listed restarts excluded',
          'players': players, 'minimum_display_minutes': 270}
(ROOT / 'data/17_passing_volume_evidence.json').write_text(json.dumps(output, indent=2))
print('Saved:', path)
plt.show()
