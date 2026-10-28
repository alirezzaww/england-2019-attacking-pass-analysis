# Soccermatics: Plotting Passes — Lucy Bronze against Sweden.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PlottingPasses.html
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Sbopen

# Load this match independently so this lesson runs from a fresh Spyder console.
parser = Sbopen()
events, related, freeze, tactics = parser.event(69301)
passes = events[events['type_name'] == 'Pass'].copy()

# The course's player map excludes throw-ins; earlier team totals included them.
player_passes = passes[
    (passes['player_name'] == 'Lucy Bronze')
    & (passes['sub_type_name'] != 'Throw-in')
].copy()
print('\nLucy Bronze pass coordinates — throw-ins excluded:')
print(player_passes[['minute', 'x', 'y', 'end_x', 'end_y', 'outcome_name']].head(10).to_string(index=False))
print('\nOutcomes (empty means completed):')
print(player_passes['outcome_name'].value_counts(dropna=False).to_string())

# A pass needs both a start point (x, y) and an end point (end_x, end_y).
assert not player_passes.empty
assert player_passes[['x', 'y', 'end_x', 'end_y']].notna().all().all()
assert player_passes[['x', 'end_x']].ge(0).all().all() and player_passes[['x', 'end_x']].le(120).all().all()
assert player_passes[['y', 'end_y']].ge(0).all().all() and player_passes[['y', 'end_y']].le(80).all().all()
completed = player_passes[player_passes['outcome_name'].isna()]
other = player_passes[player_passes['outcome_name'].notna()]

# Use the full pitch: passes happen throughout the field. Attack goes right.
pitch = Pitch(pitch_type='statsbomb', line_color='#687078')
fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.79, bottom=0.16)
pitch.arrows(completed['x'], completed['y'], completed['end_x'], completed['end_y'],
             ax=ax, color='#24658a', width=1.5, headwidth=4, headlength=4,
             alpha=0.75, label=f'Completed ({len(completed)})', zorder=3)
pitch.arrows(other['x'], other['y'], other['end_x'], other['end_y'],
             ax=ax, color='#c28a19', width=1.5, headwidth=5, headlength=5,
             alpha=0.9, label=f'Other outcomes ({len(other)})', zorder=4)
# A small dot marks where each pass started; arrowheads mark where it ended.
pitch.scatter(player_passes['x'], player_passes['y'], s=12, color='#343434', ax=ax, zorder=5)
ax.legend(loc='upper left', frameon=True, fontsize=10)
fig.suptitle('Lucy Bronze passes against Sweden', fontsize=21, fontweight='bold', y=0.96)
fig.text(0.5, 0.875, f"2019 Women's World Cup · 6 July 2019\n{len(player_passes)} attempts excluding throw-ins · England attacks left to right →", ha='center', fontsize=12)
fig.text(0.5, 0.055, 'Dots: pass starts · Arrowheads: pass ends · Source: StatsBomb Open Data · Match 69301', ha='center', fontsize=10)
figure_path = Path(__file__).resolve().parent / 'figures' / '04_lucy_bronze_pass_map.png'
figure_path.parent.mkdir(exist_ok=True)
fig.savefig(figure_path, dpi=180, bbox_inches='tight')
plt.show()
print(f'\nPlotted {len(player_passes)} attempts: {len(completed)} completed, {len(other)} other outcomes.')
print('Saved:', figure_path)
# Completion alone does not establish danger, progress, or good decision-making.

# Next lesson: describe direction using longitudinal coordinate change.
# Forward means end_x > x; it is not a formal progressive-pass metric.
player_passes['x_change'] = player_passes['end_x'] - player_passes['x']
player_passes['direction'] = 'Level (same x)'
player_passes.loc[player_passes['x_change'] > 0, 'direction'] = 'Forward'
player_passes.loc[player_passes['x_change'] < 0, 'direction'] = 'Backward'
player_passes['is_complete'] = player_passes['outcome_name'].isna()
direction_summary = player_passes.groupby('direction').agg(
    attempted=('id', 'size'),
    completed=('is_complete', 'sum')
).reindex(['Forward', 'Backward', 'Level (same x)'], fill_value=0)
direction_summary['share_pct'] = 100 * direction_summary['attempted'] / len(player_passes)
direction_summary['completion_pct'] = 100 * direction_summary['completed'] / direction_summary['attempted'].replace(0, float('nan'))
print('\nLucy Bronze pass directions — throw-ins excluded:')
print(direction_summary.round(1).to_string())
print('\nFirst five coordinate changes:')
print(player_passes[['x', 'end_x', 'x_change', 'direction']].head().to_string(index=False))
assert direction_summary['attempted'].sum() == len(player_passes)
assert direction_summary['completed'].sum() == len(completed)
# x_change is in provider coordinate units, not measured metres.
# Negative x_change does not imply a bad pass; context and available options matter.

# Next lesson: completed entries into the attacking third.
# Our definition: start x < 80, end x >= 80, and a completed pass.
# The StatsBomb pitch length is 120; the final third begins at 80.
entry_attempt_mask = (player_passes['x'] < 80) & (player_passes['end_x'] >= 80)
entry_attempts = player_passes[entry_attempt_mask].copy()
completed_entries = player_passes[entry_attempt_mask & player_passes['is_complete']].copy()
print('\nLucy Bronze attacking-third entries — throw-ins excluded:')
print(f'Attempts crossing the boundary: {len(entry_attempts)}')
print(f'Completed entries: {len(completed_entries)}')
print('\nCompleted entry coordinates:')
print(completed_entries[['minute', 'x', 'y', 'end_x', 'end_y', 'pass_recipient_name']].to_string(index=False))
assert len(completed_entries) <= len(entry_attempts)
assert completed_entries['direction'].eq('Forward').all()
# Passes starting inside the attacking third are not entries under this definition.
# A completed entry does not necessarily create a chance or break a defensive line.

# Plot just entry attempts to make the boundary crossings easy to inspect.
other_entries = entry_attempts[~entry_attempts['is_complete']].copy()
entry_pitch = Pitch(pitch_type='statsbomb', line_color='#687078')
entry_fig, entry_ax = entry_pitch.draw(figsize=(12, 8))
entry_fig.set_layout_engine(None)
entry_fig.subplots_adjust(top=0.80, bottom=0.16)
entry_ax.axvspan(80, 120, color='#e8eef2', alpha=0.6, zorder=0)
entry_ax.axvline(80, color='#454545', linestyle='--', linewidth=1.5, zorder=2)
entry_ax.text(82, 5, 'Attacking third: x ≥ 80', fontsize=11, color='#454545')
entry_pitch.arrows(completed_entries['x'], completed_entries['y'],
                   completed_entries['end_x'], completed_entries['end_y'],
                   ax=entry_ax, color='#24658a', width=2, headwidth=5,
                   headlength=5, label=f'Completed ({len(completed_entries)})', zorder=3)
entry_pitch.arrows(other_entries['x'], other_entries['y'],
                   other_entries['end_x'], other_entries['end_y'],
                   ax=entry_ax, color='#c28a19', width=2, headwidth=5,
                   headlength=5, label=f'Other outcomes ({len(other_entries)})', zorder=3)
entry_pitch.scatter(entry_attempts['x'], entry_attempts['y'], s=24,
                    color='#343434', ax=entry_ax, zorder=4)
for _, entry in completed_entries.iterrows():
    entry_pitch.annotate(entry['pass_recipient_name'].split()[-1],
                         xy=(entry['end_x'], entry['end_y']),
                         xytext=(6, -12), textcoords='offset points',
                         fontsize=10, color='#24658a', ax=entry_ax, zorder=5)
entry_ax.legend(loc='upper left', frameon=True, fontsize=10)
entry_fig.suptitle('Lucy Bronze: passes into the attacking third',
                   fontsize=20, fontweight='bold', y=0.96)
entry_fig.text(0.5, 0.875,
               f"England vs Sweden · 6 July 2019 · England attacks right →\n{len(entry_attempts)} attempts · {len(completed_entries)} completed · Throw-ins excluded",
               ha='center', fontsize=12)
entry_fig.text(0.5, 0.055,
               'Definition: start x < 80, end x ≥ 80 · Dots show starts · Source: StatsBomb Open Data, match 69301',
               ha='center', fontsize=10)
entry_map_path = Path(__file__).resolve().parent / 'figures' / '05_lucy_bronze_attacking_third_entries.png'
entry_fig.savefig(entry_map_path, dpi=180, bbox_inches='tight')
plt.show()
print('\nEntry attempt outcomes:')
print(entry_attempts['outcome_name'].value_counts(dropna=False).to_string())
# A simple width definition for this lesson; this is not a provider metric.
central_entry_count = int(completed_entries['end_y'].between(80 / 3, 160 / 3).sum())
wide_entry_count = len(completed_entries) - central_entry_count
print(f'Completed destinations in central width third: {central_entry_count}; outer width thirds: {wide_entry_count}.')
print('Saved:', entry_map_path)

# Next lesson: count who received Bronze's completed passes.
# Use only completed passes; failed passes may still name an intended recipient.
completed_player_passes = player_passes[player_passes['outcome_name'].isna()].copy()
recipient_counts = completed_player_passes['pass_recipient_name'].fillna('Not recorded').value_counts()
print('\nRecipients of Lucy Bronze completed passes — throw-ins excluded:')
print(recipient_counts.to_string())
print(f'Total completed passes accounted for: {recipient_counts.sum()}')
assert recipient_counts.sum() == len(completed_player_passes)
# Count missing recipients explicitly instead of silently dropping them.
# Frequent connections describe volume, not necessarily dangerous combinations.
