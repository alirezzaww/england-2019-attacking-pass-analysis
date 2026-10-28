# Expand the 15-second pass-before-shot analysis to the FULL England-Sweden match.
# Source: https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
import runpy
import matplotlib.pyplot as plt
from mplsoccer import Pitch

ROOT = Path(__file__).resolve().parent
# Reuse the downloaded events and the nine-pass baseline from lesson 07.
earlier = runpy.run_path(str(ROOT / '07_passes_before_shots.py'))
events = earlier['events']
TEAM = earlier['TEAM']

# The change: select England events from the ENTIRE match, with no substitution cutoff.
full_match = events[events['team_name'] == TEAM].copy()
full_match['time_seconds'] = full_match['minute'] * 60 + full_match['second']
passes = full_match[
    (full_match['type_name'] == 'Pass')
    & full_match['outcome_name'].isna()
    & (full_match['possession_team_id'] == full_match['team_id'])
    & ~full_match['sub_type_name'].isin(earlier['restarts'])
].copy()
shots = full_match[full_match['type_name'] == 'Shot'][
    ['match_id', 'period', 'possession', 'id', 'index', 'time_seconds']
].rename(columns={'id': 'shot_id', 'index': 'shot_index', 'time_seconds': 'shot_time_seconds'})

# Keep the SAME selection rules: same possession and half, completed pass, 0-15s before shot.
linked = passes.merge(shots, on=['match_id', 'period', 'possession'], how='inner')
linked['seconds_before_shot'] = linked['shot_time_seconds'] - linked['time_seconds']
qualifying = linked[
    (linked['index'] < linked['shot_index'])
    & linked['seconds_before_shot'].between(0, 15)
].copy()
danger_passes = qualifying.sort_values(['seconds_before_shot', 'shot_index']).drop_duplicates('id')
danger_passes = danger_passes.sort_values('index').reset_index(drop=True)
assert danger_passes.id.is_unique
assert danger_passes.seconds_before_shot.between(0, 15).all()
assert set(earlier['danger_passes'].id).issubset(set(danger_passes.id))
assert danger_passes[['x', 'y']].notna().all().all()
print('\nFULL-MATCH analysis:')
print(f'Eligible completed passes: {len(passes)}')
print(f'England shots: {len(shots)}')
print(f'Qualifying passes before first substitution: {len(earlier["danger_passes"])}')
print(f'Qualifying passes in full match: {len(danger_passes)}')
print(f'Shots with at least one qualifying pass: {danger_passes.shot_id.nunique()}')

pitch = Pitch(pitch_type='statsbomb', line_color='#687078', line_zorder=3)
zones = pitch.bin_statistic(danger_passes.x, danger_passes.y,
                           statistic='count', bins=(6, 5), normalize=False)
counts = zones['statistic']
assert counts.shape == (5, 6)
assert int(counts.sum()) == len(danger_passes)
print('Pass-start counts by zone:')
print(counts.astype(int))
print(f'Highest zone count: {int(counts.max())}')
fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.80, bottom=0.19)
heat = pitch.heatmap(zones, ax=ax, cmap='Blues', vmin=0, vmax=counts.max(),
                     edgecolors='#c9d0d6', linewidth=0.8)
for row in range(counts.shape[0]):
    for col in range(counts.shape[1]):
        count = int(counts[row, col])
        pitch.annotate(str(count), xy=(zones['cx'][row, col], zones['cy'][row, col]),
                       ha='center', va='center', fontsize=13, weight='bold',
                       color='white' if count > counts.max() * 0.55 else '#172d3b',
                       zorder=4, ax=ax)
fig.suptitle('England: passes shortly before shots — full match',
             fontsize=19, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         'Against Sweden · 6 July 2019 · Both halves, including added time\n'
         f'{len(danger_passes)} completed passes · Within 15 seconds before a same-possession shot · Attack →',
         ha='center', fontsize=11)
cax = fig.add_axes((0.30, 0.125, 0.40, 0.022))
cbar = fig.colorbar(heat, cax=cax, orientation='horizontal',
                    ticks=list(range(int(counts.max()) + 1)))
cbar.set_label('Qualifying passes starting in each zone', fontsize=10)
fig.text(0.5, 0.025,
         'Numbers count pass starts, not shots · Possession-team passes; listed restarts excluded\n'
         'One match describes this game, not a general team pattern · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures' / '13_england_full_match_passes_before_shots_heatmap.png'
path.parent.mkdir(exist_ok=True)
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
