# Plot the nine passes selected in lesson 07. Run this file in Spyder.
# Source lesson: https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
from pathlib import Path
import runpy
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mplsoccer import Pitch

ROOT = Path(__file__).resolve().parent
# Run the previous selection script, then reuse its data rather than change the rules.
lesson = runpy.run_path(str(ROOT / '07_passes_before_shots.py'))
danger_passes = lesson['danger_passes']
events = lesson['events']
shot_events = events[events['id'].isin(danger_passes['shot_id'].unique())]
assert len(shot_events) == danger_passes['shot_id'].nunique()
assert danger_passes[['x', 'y', 'end_x', 'end_y']].notna().all().all()

pitch = Pitch(pitch_type='statsbomb', line_color='#687078', line_zorder=1)
fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.80, bottom=0.18)

# A dot shows the pass START. The arrow points to the recorded pass END.
pitch.arrows(danger_passes.x, danger_passes.y, danger_passes.end_x, danger_passes.end_y,
             width=2.5, headwidth=4, headlength=4, color='#24658a', alpha=0.8,
             zorder=2, ax=ax)
pitch.scatter(danger_passes.x, danger_passes.y, s=65, color='#24658a',
              edgecolors='white', linewidths=0.8, zorder=3, ax=ax)
pitch.scatter(shot_events.x, shot_events.y, s=250, marker='*', color='#222222',
              edgecolors='white', linewidths=0.8, zorder=4, ax=ax)

# Highlight the concrete example from lesson 07.
example = danger_passes.iloc[0]
pitch.arrows(example.x, example.y, example.end_x, example.end_y,
             width=3, headwidth=4, headlength=4, color='#b77516', zorder=5, ax=ax)
pitch.scatter(example.x, example.y, s=85, color='#b77516',
              edgecolors='white', linewidths=0.8, zorder=6, ax=ax)
pitch.annotate(
    f"{example.player_name.split()[-1]}'s pass at {int(example.minute):02d}:{int(example.second):02d}\n"
    f"{int(example.seconds_before_shot)} seconds before {example.shooter.split()[-1]}'s shot",
    xy=(example.x, example.y), xytext=(35, 12), ha='center', va='center', fontsize=10,
    bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#b77516'),
    arrowprops=dict(arrowstyle='->', color='#b77516'), zorder=7, ax=ax
)
fig.suptitle('England: completed passes shortly before shots',
             fontsize=20, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         f"Against Sweden · 6 July 2019 · Before England’s first substitution (49:23)\n"
         f'{len(danger_passes)} passes · Within 15 seconds before a same-possession England shot · Attack →',
         ha='center', fontsize=11)
handles = [
    Line2D([0], [0], color='#24658a', marker='o', lw=2, label='Qualifying pass: start → end'),
    Line2D([0], [0], color='#b77516', marker='o', lw=2, label='White example'),
    Line2D([0], [0], color='#222222', marker='*', markersize=12, lw=0,
           label=f'{len(shot_events)} associated shots'),
]
fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.095),
           ncol=3, frameon=False, columnspacing=2)
fig.text(0.5, 0.025,
         'Possession-team completed passes · Listed restarts excluded · Some arrows overlap\n'
         'Passes counted once; several may precede one shot · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
path = ROOT / 'figures' / '11_england_passes_before_shots.png'
path.parent.mkdir(exist_ok=True)
fig.savefig(path, dpi=180, bbox_inches='tight')
print('Saved:', path)
plt.show()
