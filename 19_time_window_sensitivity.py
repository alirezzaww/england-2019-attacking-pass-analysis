"""Lesson 19: does a 5, 10 or 15 second selection window change the comparison?

Extension of Soccermatics' 15-second pass heatmap method:
https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
Run in Spyder or a terminal. Uses saved evidence; no new download is needed.
"""
from collections import Counter
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())
# The nearest eligible shot was already selected AFTER the xG > 0.10 filter.
# If that shot is more than 5 seconds away, no other eligible shot can be closer.
# Therefore filtering these nearest-shot gaps gives the same shorter-window sets.
baseline = source['selected_passes']['0.10']
WINDOWS = [5, 10, 15]
HIGHLIGHTS = ['Francesca Kirby', 'Nikita Parris', 'Keira Walsh', 'Lucy Bronze']
results = {}
for window in WINDOWS:
    selected = [p for p in baseline if 0 <= p['seconds_before_shot'] <= window]
    counts = Counter(p['player_id'] for p in selected)
    players = []
    for player in source['players']:
        count = counts[player['player_id']]
        players.append({
            'player_id': player['player_id'], 'player_name': player['player_name'],
            'minutes': player['minutes'], 'count': count,
            'per90': count / player['minutes'] * 90,
        })
    results[str(window)] = {'total': len(selected), 'selected_passes': selected, 'players': players}
    print(f'Within {window} seconds: {len(selected)} qualifying passes')
    for player in players:
        if player['player_name'] in HIGHLIGHTS:
            print(f"  {player['player_name']}: {player['count']} passes; {player['per90']:.2f} per 90")

identities = lambda rows: {(p['match_id'], p['id']) for p in rows}
assert identities(results['5']['selected_passes']) <= identities(results['10']['selected_passes'])
assert identities(results['10']['selected_passes']) <= identities(baseline)
assert results['15']['total'] == len(baseline) == 98
output = {
    'windows_seconds_inclusive': WINDOWS,
    'xg_threshold_strictly_greater_than': 0.10,
    'timing': 'nominal minute * 60 + second, not subsecond timestamps',
    'matching': 'Nearest subsequent eligible shot by nominal gap then event index; same match, period and possession',
    'minutes_source': '14_threshold_sensitivity_evidence.json',
    'windows': results,
    'highlight_players': HIGHLIGHTS,
}
(ROOT / 'data/19_time_window_evidence.json').write_text(json.dumps(output, indent=2))

fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.subplots_adjust(left=0.07, right=0.97, bottom=0.23, top=0.76, wspace=0.28)
axes[0].bar([str(w) for w in WINDOWS], [results[str(w)]['total'] for w in WINDOWS], color='#24658a', width=0.55)
for i, window in enumerate(WINDOWS):
    total = results[str(window)]['total']
    axes[0].text(i, total + 1.5, str(total), ha='center', weight='bold')
axes[0].set_ylim(0, 115)
axes[0].set_xlabel('Maximum seconds before the shot (inclusive)')
axes[0].set_ylabel('Qualifying completed passes across seven matches')
axes[0].set_title('How much involvement is selected?')
colors = ['#24658a', '#b77516', '#527956', '#8b537c']
for name, color in zip(HIGHLIGHTS, colors):
    rates = [next(p['per90'] for p in results[str(w)]['players'] if p['player_name'] == name) for w in WINDOWS]
    axes[1].plot(WINDOWS, rates, marker='o', color=color, label=name.split()[-1], linewidth=2)
axes[1].set_xticks(WINDOWS)
axes[1].set_ylim(bottom=0)
axes[1].set_xlabel('Maximum seconds before the shot (inclusive)')
axes[1].set_ylabel('Qualifying passes per 90 reconstructed minutes')
axes[1].set_title('Four previously profiled players')
axes[1].legend(frameon=False, fontsize=9, ncol=2)
for ax in axes:
    ax.grid(axis='y', color='#e4e7ea')
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
fig.suptitle('England: does the time window change the result?', fontsize=19, weight='bold', y=0.96)
fig.text(0.5, 0.84, '2019 Women’s World Cup · Seven matches · Shot xG > 0.10 throughout\nSame possession, pass rules and playing-time denominators at every window', ha='center', fontsize=11)
fig.text(0.5, 0.055, 'A shorter window selects involvement closer in time; it does not prove an assist or causal impact.\nNested selections, not independent samples or confidence intervals · Nominal second timing · Source: StatsBomb Open Data', ha='center', fontsize=9)
path = ROOT / 'figures/22_time_window_sensitivity.png'
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
