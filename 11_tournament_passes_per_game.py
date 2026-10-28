# Soccermatics Pass heat maps: England's 2019 World Cup, counts per TEAM game.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Sbopen

ROOT = Path(__file__).resolve().parent
TEAM = "England Women's"
matches = Sbopen().match(competition_id=72, season_id=30)
team_matches = matches[
    (matches.home_team_name == TEAM) | (matches.away_team_name == TEAM)
].sort_values('match_date').reset_index(drop=True)
match_ids = team_matches.match_id.tolist()
no_games = len(match_ids)
assert no_games > 1 and len(set(match_ids)) == no_games
print(f'Loading {no_games} England matches...', flush=True)

# Download independent matches together. The filtering below remains the same.
def load_events(match_id):
    return Sbopen().event(int(match_id))[0]

with ThreadPoolExecutor(max_workers=3) as pool:
    frames = list(pool.map(load_events, match_ids))
assert len(frames) == no_games and all(not frame.empty for frame in frames)
events = pd.concat(frames, ignore_index=True)
assert events[['match_id', 'id']].duplicated().sum() == 0
assert set(events.match_id) == set(match_ids)
team_events = events[events.team_name == TEAM].copy()
team_events['time_seconds'] = team_events.minute * 60 + team_events.second
restarts = ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']
passes = team_events[
    (team_events.type_name == 'Pass') & team_events.outcome_name.isna()
    & (team_events.possession_team_id == team_events.team_id)
    & ~team_events.sub_type_name.isin(restarts)
].copy()
shots = team_events[team_events.type_name == 'Shot'][
    ['match_id', 'period', 'possession', 'id', 'index', 'time_seconds']
].rename(columns={'id': 'shot_id', 'index': 'shot_index', 'time_seconds': 'shot_time_seconds'})
linked = passes.merge(shots, on=['match_id', 'period', 'possession'], how='inner')
linked['seconds_before_shot'] = linked.shot_time_seconds - linked.time_seconds
qualifying = linked[
    (linked['index'] < linked.shot_index) & linked.seconds_before_shot.between(0, 15)
]
danger_passes = qualifying.sort_values(['seconds_before_shot', 'shot_index']).drop_duplicates(['match_id', 'id'])
danger_passes = danger_passes.sort_values(['match_id', 'index']).reset_index(drop=True)
assert danger_passes[['x', 'y']].notna().all().all()
assert danger_passes.x.between(0, 120).all() and danger_passes.y.between(0, 80).all()

# Include every team match in the denominator, even one with zero qualifying passes.
per_match = danger_passes.groupby('match_id').size().reindex(match_ids, fill_value=0)
assert per_match.sum() == len(danger_passes)
# Reproduce our earlier full-match result for the Sweden game.
assert int(per_match.loc[69301]) == 18
print('\nQualifying passes in each match:')
for match in team_matches.itertuples():
    opponent = match.away_team_name if match.home_team_name == TEAM else match.home_team_name
    print(f'{str(match.match_date)[:10]} vs {opponent}: {int(per_match.loc[match.match_id])}')
print(f'\nTotal: {len(danger_passes)}; games: {no_games}; per game: {len(danger_passes) / no_games:.2f}')

pitch = Pitch(pitch_type='statsbomb', line_color='#687078', line_zorder=3)
zones = pitch.bin_statistic(danger_passes.x, danger_passes.y, statistic='count', bins=(6, 5))
raw_counts = zones['statistic'].copy()
assert int(raw_counts.sum()) == len(danger_passes)

# This is the new calculation: divide each zone's TOTAL by ALL England games.
zones['statistic'] = raw_counts / no_games
rates = zones['statistic']
assert np.isclose(rates.sum(), len(danger_passes) / no_games)
print('Raw pass-start counts by zone:')
print(raw_counts.astype(int))
print('Pass starts per team game by zone:')
print(rates.round(2))

fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.80, bottom=0.19)
heat = pitch.heatmap(zones, ax=ax, cmap='Blues', vmin=0, vmax=rates.max(),
                     edgecolors='#c9d0d6', linewidth=0.8)
for row in range(rates.shape[0]):
    for col in range(rates.shape[1]):
        value = rates[row, col]
        pitch.annotate(f'{value:.1f}', xy=(zones['cx'][row, col], zones['cy'][row, col]),
                       ha='center', va='center', fontsize=13, weight='bold',
                       color='white' if value > rates.max() * 0.55 else '#172d3b', zorder=4, ax=ax)
fig.suptitle('England: passes shortly before shots, per game',
             fontsize=20, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         f"2019 Women's World Cup · {str(team_matches.match_date.min())[:10]} to {str(team_matches.match_date.max())[:10]}\n"
         f'{len(danger_passes)} qualifying passes ÷ {no_games} team games = {len(danger_passes) / no_games:.1f} per game · Attack →',
         ha='center', fontsize=11)
cax = fig.add_axes((0.30, 0.125, 0.40, 0.022))
cbar = fig.colorbar(heat, cax=cax, orientation='horizontal')
cbar.set_label('Qualifying pass starts per team game in each zone', fontsize=10)
fig.text(0.5, 0.025,
         'Completed possession-team passes within 15s before a same-possession shot; listed restarts excluded\n'
         'Zone labels rounded to 1 decimal · Per team game, not per 90 minutes or possession · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
(ROOT / 'figures').mkdir(exist_ok=True)
(ROOT / 'data').mkdir(exist_ok=True)
path = ROOT / 'figures' / '14_england_tournament_passes_before_shots_per_game.png'
fig.savefig(path, dpi=180, bbox_inches='tight')

# Inspectable evidence: raw counts, exact rates, match counts and selected events.
evidence = {
    'team': TEAM, 'competition_id': 72, 'season_id': 30,
    'games': no_games, 'match_ids': [int(value) for value in match_ids],
    'total_qualifying_passes': len(danger_passes),
    'per_match_counts': {str(key): int(value) for key, value in per_match.items()},
    'raw_zone_counts': raw_counts.astype(int).tolist(), 'zone_rates_per_game': rates.tolist(),
    'selected_passes': danger_passes[
        ['match_id', 'id', 'player_name', 'x', 'y', 'end_x', 'end_y',
         'shot_id', 'seconds_before_shot']
    ].to_dict(orient='records')
}
(ROOT / 'data' / '11_tournament_passes_evidence.json').write_text(json.dumps(evidence, indent=2))
print('Saved:', path)
plt.show()
