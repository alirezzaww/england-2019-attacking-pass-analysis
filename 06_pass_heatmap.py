# Beginner preparation for Soccermatics' Pass heat maps lesson.
# The full tutorial maps passes before shots across a tournament.
# Here we first learn the grid using our existing single-match selection.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Sbopen

ROOT = Path(__file__).resolve().parent
events, related, freeze, tactics = Sbopen().event(69301)
TEAM = "England Women's"
first_sub = events[
    (events['type_name'] == 'Substitution') & (events['team_name'] == TEAM)
].sort_values('index').iloc[0]

# Same 220 completed passes as our original network, in every direction.
passes = events[
    (events['type_name'] == 'Pass')
    & (events['team_name'] == TEAM)
    & (events['index'] < first_sub['index'])
    & events['outcome_name'].isna()
    & (events['sub_type_name'] != 'Throw-in')
].copy()
assert not passes.empty
assert passes[['x', 'y']].notna().all().all()
assert passes.x.between(0, 120).all() and passes.y.between(0, 80).all()

# Divide the pitch into six columns and five rows = 30 equal zones.
# Count START locations: x and y, not end_x and end_y.
pitch = Pitch(pitch_type='statsbomb', line_color='#424b52', line_zorder=3)
zones = pitch.bin_statistic(passes['x'], passes['y'],
                           statistic='count', bins=(6, 5), normalize=False)
counts = zones['statistic']
assert counts.shape == (5, 6)
assert int(counts.sum()) == len(passes)
print(f'Completed passes counted: {len(passes)}')
print('Grid: 6 columns x 5 rows = 30 zones.')
print('Each zone spans 20 x units and 16 y units.')
print('Numbers below count where passes STARTED, not where players stood all match:')
print(counts.astype(int))
print(f'Highest zone count: {int(counts.max())}')

fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.80, bottom=0.19)
heat = pitch.heatmap(zones, ax=ax, cmap='Blues', vmin=0,
                     edgecolors='#c9d0d6', linewidth=0.8)
# Show exact counts as well as colour, including zero-pass zones.
for row in range(counts.shape[0]):
    for col in range(counts.shape[1]):
        count = int(counts[row, col])
        pitch.annotate(str(count), xy=(zones['cx'][row, col], zones['cy'][row, col]),
                       ha='center', va='center', fontsize=13, weight='bold',
                       color='white' if count > counts.max() * 0.55 else '#172d3b',
                       zorder=4, ax=ax)
fig.suptitle('England: where completed passes started',
             fontsize=20, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         f"Against Sweden · 6 July 2019 · Before England’s first substitution ({int(first_sub['minute'])}:{int(first_sub['second']):02d})\n"
         f'{len(passes)} completed passes · All directions · Throw-ins excluded · Attack →',
         ha='center', fontsize=11)
cax = fig.add_axes((0.30, 0.125, 0.40, 0.022))
cbar = fig.colorbar(heat, cax=cax, orientation='horizontal')
cbar.set_label('Completed passes starting in each zone', fontsize=10)
fig.text(0.5, 0.025,
         'Darker blue = more pass starts · Numbers are counts, not percentages\n'
         '6 columns × 5 rows · Passing frequency does not measure danger · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures' / '10_england_pass_start_heatmap.png'
path.parent.mkdir(exist_ok=True)
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
