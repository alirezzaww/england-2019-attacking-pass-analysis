# Soccermatics: which players made the passes shortly before shots?
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
# Run lesson 11 first to generate the saved tournament evidence.
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
evidence_path = ROOT / 'data' / '11_tournament_passes_evidence.json'
evidence = json.loads(evidence_path.read_text())
passes = pd.DataFrame(evidence['selected_passes'])
no_games = evidence['games']
assert no_games > 0
assert not passes.duplicated(['match_id', 'id']).any()
assert len(passes) == evidence['total_qualifying_passes']

# Count all selected passes by their passer, not their recipient or shooter.
players = passes.groupby('player_name').size().reset_index(name='total_passes')
players['per_team_game'] = players['total_passes'] / no_games
players = players.sort_values(['total_passes', 'player_name'], ascending=[False, True])
assert players.total_passes.sum() == len(passes)
print(f'{len(passes)} qualifying passes across {no_games} England games.')
print(players.round(2).to_string(index=False))
print('\nPer team game = player total / ALL England games.')
print('This is not per appearance or per 90 minutes; playing time is not adjusted.')

top = players.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(12, 8))
fig.subplots_adjust(left=0.22, right=0.95, top=0.80, bottom=0.20)
ax.barh(top.player_name, top.per_team_game, color='#24658a', height=0.65, zorder=3)
for row in top.itertuples():
    ax.text(row.per_team_game + 0.08, row.player_name,
            f'{row.per_team_game:.2f} ({row.total_passes} total)',
            ha='left', va='center', fontsize=11)
ax.set_xlim(0, top.per_team_game.max() + 1.7)
ax.set_xlabel('Qualifying passes per England team game', fontsize=11, labelpad=10)
ax.tick_params(axis='both', labelsize=11, length=0)
ax.grid(axis='x', color='#e4e7ea', linewidth=0.8, zorder=0)
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color('#687078')
fig.suptitle('England: players making passes shortly before shots',
             fontsize=19, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         f"2019 Women's World Cup · 9 June–6 July 2019 · {no_games} England games\n"
         'Top 10 by total qualifying passes · Labels: per team game (tournament total)',
         ha='center', fontsize=11)
fig.text(0.5, 0.055,
         'Completed possession-team passes within 15s before a same-possession England shot; listed restarts excluded\n'
         'Divide by all team games, not player appearances · No playing-time adjustment · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures' / '15_england_players_passes_before_shots.png'
path.parent.mkdir(exist_ok=True)
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
