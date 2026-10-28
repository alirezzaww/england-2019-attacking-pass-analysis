# Practical player profile: inspect the individual events behind a summary rate.
from pathlib import Path
from collections import Counter
import json
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mplsoccer import Pitch

ROOT = Path(__file__).resolve().parent
PLAYER = 'Francesca Kirby'  # chosen from the preceding lesson, before inspecting this map
evidence = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())
rows = [p for p in evidence['selected_passes']['0.10'] if p['player_name'] == PLAYER]
assert rows
events_by_match = {}
records = []
for row in rows:
    mid = row['match_id']
    if mid not in events_by_match:
        raw = json.loads((ROOT / f'data/cache_2019_events/{mid}.json').read_text())
        events_by_match[mid] = {e['id']: e for e in raw}
    event = events_by_match[mid][row['id']]
    end_x, end_y = event['pass']['end_location'][:2]
    records.append({**row, 'end_x': end_x, 'end_y': end_y,
                    'recipient': event['pass'].get('recipient', {}).get('name'),
                    'minute': event['minute'], 'second': event['second']})

# A direction classification is distinct from a valuation of the pass.
forward = sum(p['end_x'] > p['x'] for p in records)
backward = sum(p['end_x'] < p['x'] for p in records)
level = sum(p['end_x'] == p['x'] for p in records)
final_third_entries = sum(p['x'] < 80 <= p['end_x'] for p in records)
final_third_starts = sum(p['x'] >= 80 for p in records)
assert forward + backward + level == len(records)
player = next(p for p in evidence['players'] if p['player_name'] == PLAYER)
print(f'{PLAYER}: {len(records)} passes before shots with xG > 0.10')
print(f'{player["minutes"]:.2f} reconstructed minutes; {player["per90_010"]:.2f} per 90')
print(f'Direction: {forward} forward, {backward} backward, {level} level in x')
print(f'Final-third entries (start x < 80, end x >= 80): {final_third_entries}')
print(f'Passes starting already inside the final third: {final_third_starts}')
print('Recipients:',Counter(p['recipient'] for p in records))
print('Passes per match:',Counter(p['match_id'] for p in records))

# Two linked maps: exact pass arrows and a count of the SAME pass starts by zone.
pitch = Pitch(pitch_type='statsbomb', line_color='#687078', line_zorder=2)
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.subplots_adjust(top=0.80, bottom=0.19, left=0.03, right=0.97, wspace=0.10)
for ax in axes:
    pitch.draw(ax=ax)
    ax.axvline(80, color='#687078', ls='--', lw=1, zorder=2)
for p in records:
    color = '#b77516' if p['x'] < 80 <= p['end_x'] else '#24658a'
    pitch.arrows(p['x'], p['y'], p['end_x'], p['end_y'], color=color, width=1.8,
                 headwidth=4, headlength=4, alpha=0.8, ax=axes[0], zorder=3)
    pitch.scatter(p['x'], p['y'], color=color, edgecolors='white', s=35,
                  linewidths=0.6, ax=axes[0], zorder=4)
zones = pitch.bin_statistic([p['x'] for p in records], [p['y'] for p in records],
                           statistic='count', bins=(6, 5), normalize=False)
counts = zones['statistic']
assert int(counts.sum()) == len(records)
pitch.heatmap(zones, ax=axes[1], cmap='Blues', vmin=0, vmax=counts.max(), edgecolors='#c9d0d6')
for i in range(counts.shape[0]):
    for j in range(counts.shape[1]):
        n = int(counts[i, j])
        pitch.annotate(str(n), xy=(zones['cx'][i, j], zones['cy'][i, j]), ha='center', va='center',
                       fontsize=10, color='white' if n > counts.max() * 0.55 else '#172d3b', ax=axes[1], zorder=4)
axes[0].set_title('Individual passes: dot = start; arrowhead = end', fontsize=12)
axes[0].legend(handles=[Line2D([0], [0], color='#b77516', lw=2, label='Entry into final third'),
                       Line2D([0], [0], color='#24658a', lw=2, label='Other selected pass')],
               loc='lower left', bbox_to_anchor=(0.02, 0.12), frameon=False, fontsize=9)
axes[1].set_title(f'Pass-start counts by zone; labels sum to {len(records)}', fontsize=12)
fig.suptitle(f'{PLAYER}: examine the events behind the rate', fontsize=20, weight='bold', y=0.96)
fig.text(0.5, 0.86,
         f'2019 Women’s World Cup · Seven England games · {len(records)} passes before shots with xG > 0.10\n'
         f'{player["per90_010"]:.2f} per 90 reconstructed minutes · {forward} forward, {backward} backward · Attack →',
         ha='center', fontsize=12)
fig.text(0.5, 0.065,
         'Same-possession, completed passes within 15 seconds before an above-threshold shot; listed restarts excluded\n'
         'Dashed line: final third starts at x = 80 · Heatmap counts starts, not endpoints · All other passes are omitted\n'
         'Describes this selected sample; does not establish overall player quality · Source: StatsBomb Open Data', ha='center', fontsize=10)
figure = ROOT / 'figures/18_kirby_passes_before_shots_profile.png'
fig.savefig(figure, dpi=180, bbox_inches='tight')
(ROOT / 'data/15_kirby_profile_evidence.json').write_text(json.dumps(
    {'player': PLAYER, 'xg_threshold_strictly_greater_than': 0.10, 'minutes': player['minutes'],
     'per90': player['per90_010'], 'forward': forward, 'backward': backward, 'level': level,
     'final_third_entries': final_third_entries, 'final_third_starts': final_third_starts,
     'selected_passes': records}, indent=2))
print('Saved:',figure)
plt.show()
