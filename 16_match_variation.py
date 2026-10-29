# Project extension: variability, zero counts, absence, and weighted per-90 rates.
from pathlib import Path
from collections import Counter
import json
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
PLAYER = 'Francesca Kirby'
timed = json.loads((ROOT / 'data/13_minutes_and_quality_evidence.json').read_text())
selected = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())
base = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
passes = [p for p in selected['selected_passes']['0.10'] if p['player_name'] == PLAYER]
counts = Counter(p['match_id'] for p in passes)
rows = []
for match_id in base['match_ids']:
    minutes = sum(p['minutes'] for p in timed['player_intervals']
                  if p['match_id'] == match_id and p['player_name'] == PLAYER)
    events = json.loads((ROOT / f'data/cache_2019_events/{match_id}.json').read_text())
    opponent = next(e['team']['name'] for e in events if e['team']['name'] != "England Women's")
    opponent = opponent.replace(" Women's", '').removesuffix(' W')
    count = counts[match_id]
    assert minutes > 0 or count == 0
    rows.append({'match_id': match_id, 'opponent': opponent, 'minutes': minutes,
                 'qualifying_passes': count,
                 'per90': count / minutes * 90 if minutes > 0 else None})

total = sum(r['qualifying_passes'] for r in rows)
minutes = sum(r['minutes'] for r in rows)
tournament_per90 = total / minutes * 90
appearances = [r for r in rows if r['minutes'] > 0]
unweighted_mean = sum(r['per90'] for r in appearances) / len(appearances)
weighted_mean = sum(r['per90'] * r['minutes'] for r in appearances) / minutes
assert np.isclose(tournament_per90, weighted_mean)
assert total == len(passes) == 12
player_summary = next(p for p in selected['players'] if p['player_name'] == PLAYER)
assert np.isclose(minutes, player_summary['minutes'])
assert np.isclose(tournament_per90, player_summary['per90_010'])

# Recalculate the tournament rate after omitting one appearance at a time.
# This is a sensitivity check, not a confidence interval or prediction.
leave_one_out = []
for row in appearances:
    rate = (total - row['qualifying_passes']) / (minutes - row['minutes']) * 90
    leave_one_out.append({'omitted_match_id': row['match_id'], 'opponent': row['opponent'],
                          'remaining_passes': total - row['qualifying_passes'],
                          'remaining_minutes': minutes - row['minutes'], 'per90': rate})
print(PLAYER, '— passes before shots with xG > 0.10')
for row in rows:
    rate = f'{row["per90"]:.2f}' if row['per90'] is not None else 'DNP'
    print(f'{row["opponent"]:15} {row["minutes"]:6.1f} min; '
          f'{row["qualifying_passes"]} passes; per90: {rate}')
print(f'Tournament rate (sum counts / sum minutes * 90): {tournament_per90:.2f}')
print(f'Unweighted mean of appearance rates (different estimand): {unweighted_mean:.2f}')
print('Leave-one-appearance-out rates:')
for row in leave_one_out:
    print(f'Without {row["opponent"]}: {row["per90"]:.2f}')

fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharey=True)
fig.subplots_adjust(left=0.20, right=0.97, top=0.80, bottom=0.22, wspace=0.15)
y = np.arange(len(rows))
axes[0].barh(y, [r['qualifying_passes'] for r in rows], height=0.6, color='#24658a')
for i, row in enumerate(rows):
    if row['minutes'] > 0:
        axes[0].text(row['qualifying_passes'] + 0.08, i,
                     str(row['qualifying_passes']), va='center', fontsize=11)
        axes[1].barh(i, row['per90'], height=0.6, color='#b77516')
        axes[1].text(row['per90'] + 0.08, i, f'{row["per90"]:.2f}', va='center', fontsize=11)
    else:
        for ax in axes:
            ax.text(0.08, i, 'Did not play', va='center', fontsize=11, color='#687078')
axes[0].set_yticks(y, [f'{r["opponent"]} ({r["minutes"]:.0f} min)' for r in rows], fontsize=11)
axes[0].invert_yaxis()
axes[0].set_xlim(0, 5)
axes[1].set_xlim(0, 5.2)
axes[0].set_xlabel('Qualifying passes: match total', fontsize=11)
axes[1].set_xlabel('Qualifying passes per 90 reconstructed minutes', fontsize=10)
axes[0].set_title('What happened in each match?', fontsize=12)
axes[1].set_title('How often, relative to playing time?', fontsize=12)
axes[1].axvline(tournament_per90, color='#444444', ls='--', lw=1.2,
                label=f'Tournament rate: {tournament_per90:.2f}')
axes[1].legend(loc='lower right', frameon=False, fontsize=10)
for ax in axes:
    ax.grid(axis='x', color='#e4e7ea')
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0)
    for side in ['top', 'right', 'left']:
        ax.spines[side].set_visible(False)
fig.suptitle('Kirby: the tournament average hides match variation', fontsize=20, weight='bold', y=0.96)
fig.text(0.5, 0.875,
         '2019 Women’s World Cup · Fixtures in chronological order, 9 June–6 July\n'
         'Completed passes within 15 seconds before same-possession shots with xG > 0.10',
         ha='center', fontsize=11)
fig.text(0.5, 0.055,
         'Zero = played, but no pass met this definition · Did not play = no per-90 rate\n'
         'Minutes include added time; halftime excluded; temporary injury absences retained\n'
         'Roles, opposition and game state are not adjusted · Source: StatsBomb Open Data',
         ha='center', fontsize=10)
path = ROOT / 'figures/19_kirby_match_variation.png'
fig.savefig(path, dpi=180, bbox_inches='tight')
output = {'player': PLAYER, 'xg_threshold_strictly_greater_than': 0.10,
          'matches': rows, 'total_passes': total, 'total_minutes': minutes,
          'tournament_per90': tournament_per90,
          'unweighted_mean_of_appearance_rates': unweighted_mean,
          'leave_one_appearance_out': leave_one_out,
          'note': 'Leave-one-out results are sensitivity checks, not confidence intervals.'}
(ROOT / 'data/16_match_variation_evidence.json').write_text(json.dumps(output, indent=2))
print('Saved:', path)
plt.show()
