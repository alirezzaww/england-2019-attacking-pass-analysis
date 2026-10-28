# Soccermatics: count where passes shortly before shots STARTED.
# Single-match-window preparation for the tutorial's tournament-wide heatmap.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
import runpy
import matplotlib.pyplot as plt
from mplsoccer import Pitch

ROOT = Path(__file__).resolve().parent
lesson = runpy.run_path(str(ROOT / '07_passes_before_shots.py'))
danger_passes = lesson['danger_passes']
assert not danger_passes.empty
assert danger_passes[['x', 'y']].notna().all().all()

# Use exactly the same 6-column, 5-row grid as our first heatmap.
pitch = Pitch(pitch_type='statsbomb', line_color='#687078', line_zorder=3)
zones = pitch.bin_statistic(danger_passes.x, danger_passes.y,
                           statistic='count', bins=(6, 5), normalize=False)
counts = zones['statistic']
assert counts.shape == (5, 6)
assert int(counts.sum()) == len(danger_passes)
print('\nPass starts per zone (top row of pitch first):')
print(counts.astype(int))
print(f'Total across zones: {int(counts.sum())}')
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
fig.suptitle('England: where passes shortly before shots started',
             fontsize=19, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         'Against Sweden · 6 July 2019 · Before England’s first substitution (49:23)\n'
         f'{len(danger_passes)} completed passes · Within 15 seconds before a same-possession shot · Attack →',
         ha='center', fontsize=11)
cax = fig.add_axes((0.30, 0.125, 0.40, 0.022))
cbar = fig.colorbar(heat, cax=cax, orientation='horizontal',
                    ticks=list(range(int(counts.max()) + 1)))
cbar.set_label('Qualifying passes starting in each zone', fontsize=10)
fig.text(0.5, 0.025,
         'Numbers count pass starts, not shots · Possession-team passes; listed restarts excluded\n'
         'Only 9 passes in this selection: describe this period, not a general team pattern · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures' / '12_england_passes_before_shots_heatmap.png'
path.parent.mkdir(exist_ok=True)
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
