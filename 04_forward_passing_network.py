# Soccermatics challenge: England's network using completed FORWARD passes only.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html#challenge
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mplsoccer import Pitch, Sbopen

ROOT = Path(__file__).resolve().parent
events, related, freeze, tactics = Sbopen().event(69301)
TEAM = "England Women's"
first_sub = events[
    (events['type_name'] == 'Substitution') & (events['team_name'] == TEAM)
].sort_values('index').iloc[0]
completed_passes = events[
    (events['type_name'] == 'Pass')
    & (events['team_name'] == TEAM)
    & (events['index'] < first_sub['index'])
    & events['outcome_name'].isna()
    & (events['sub_type_name'] != 'Throw-in')
].copy()

# In StatsBomb event coordinates the team attacks toward x = 120.
# Forward means the pass finishes farther along that axis than it starts.
forward_passes = completed_passes[
    completed_passes['end_x'] > completed_passes['x']
].copy()
assert not forward_passes.empty
assert forward_passes[['player_name', 'pass_recipient_name', 'x', 'y', 'end_x', 'end_y']].notna().all().all()
print(f'All completed passes in selected period: {len(completed_passes)}')
print(f'Forward completed passes: {len(forward_passes)} ({len(forward_passes) / len(completed_passes):.1%})')

# Extra practice: a player's forward share among her COMPLETED passes.
# This is not forward-pass completion rate: failed attempts are not in this denominator.
player_comparison = completed_passes.groupby('player_name').size().to_frame('completed_passes')
player_comparison['forward_completed'] = forward_passes.groupby('player_name').size().reindex(
    player_comparison.index, fill_value=0
)
player_comparison['forward_share_pct'] = (
    player_comparison['forward_completed'] / player_comparison['completed_passes'] * 100
)
assert player_comparison['completed_passes'].sum() == len(completed_passes)
assert player_comparison['forward_completed'].sum() == len(forward_passes)
assert player_comparison['forward_share_pct'].between(0, 100).all()
print('\nForward share among each player\'s completed passes (%):')
print(player_comparison.sort_values('forward_completed', ascending=False).round(1).to_string())

# Recalculate locations and sizes using ONLY the selected forward passes.
starts = forward_passes[['player_name', 'x', 'y']]
ends = forward_passes[['pass_recipient_name', 'end_x', 'end_y']].rename(
    columns={'pass_recipient_name': 'player_name', 'end_x': 'x', 'end_y': 'y'}
)
nodes = pd.concat([starts, ends], ignore_index=True).groupby('player_name')[['x', 'y']].mean()
nodes['forward_passes_made'] = forward_passes.groupby('player_name').size().reindex(nodes.index, fill_value=0)
assert nodes['forward_passes_made'].sum() == len(forward_passes)
nodes['marker_area'] = nodes['forward_passes_made'] / nodes['forward_passes_made'].max() * 1600

# Keep both the directed counts and the combined pair counts for inspection.
directed = forward_passes.groupby(['player_name', 'pass_recipient_name']).size().reset_index(name='pass_count')
pair_rows = pd.DataFrame(
    [sorted([row.player_name, row.pass_recipient_name]) for row in directed.itertuples()],
    columns=['player_1', 'player_2']
)
pair_rows['pass_count'] = directed['pass_count']
pairs = pair_rows.groupby(['player_1', 'player_2'])['pass_count'].sum().reset_index()
pairs = pairs.sort_values('pass_count', ascending=False).reset_index(drop=True)
assert pairs.pass_count.sum() == len(forward_passes)
visible = pairs[pairs['pass_count'] >= 3]
assert not visible.empty
print('\nMost completed forward passes made:')
print(nodes['forward_passes_made'].sort_values(ascending=False).to_string())
print('\nTop forward-pass connections (both directions combined):')
print(pairs.head(5).to_string(index=False))
print(f'Visible links: {len(visible)}; forward passes represented by links: {visible.pass_count.sum()}')

pitch = Pitch(pitch_type='statsbomb', line_color='#687078')
fig, ax = pitch.draw(figsize=(12, 8))
fig.set_layout_engine(None)
fig.subplots_adjust(top=0.80, bottom=0.21)
max_pair = visible.pass_count.max()
for pair in visible.itertuples():
    a, b = nodes.loc[pair.player_1], nodes.loc[pair.player_2]
    pitch.lines(a.x, a.y, b.x, b.y, lw=pair.pass_count / max_pair * 10,
                color='#24658a', alpha=0.55, zorder=2, ax=ax)
pitch.scatter(nodes.x, nodes.y, s=nodes.marker_area, color='#24658a',
              edgecolors='white', linewidths=1.5, zorder=3, ax=ax)
for name, node in nodes.iterrows():
    pitch.annotate(name.split()[-1], xy=(node.x, node.y), xytext=(0, 22),
                   textcoords='offset points', ha='center', fontsize=11, zorder=4, ax=ax)
top = pairs.iloc[0]
a, b = nodes.loc[top.player_1], nodes.loc[top.player_2]
pitch.annotate(f'{top.pass_count} forward passes', xy=((a.x + b.x) / 2, (a.y + b.y) / 2),
               xytext=(-115, 0), textcoords='offset points', ha='center', fontsize=9,
               bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#24658a'),
               arrowprops=dict(arrowstyle='->', color='#24658a'), zorder=5, ax=ax)
fig.suptitle('England: completed forward-pass network', fontsize=20, fontweight='bold', y=0.96)
fig.text(0.5, 0.875,
         f"Against Sweden · 6 July 2019 · Before first England substitution ({int(first_sub['minute'])}:{int(first_sub['second']):02d})\n"
         f"{len(forward_passes)} forward completed passes · end_x > x · Throw-ins excluded · Attack →",
         ha='center', fontsize=11)
handles = [Line2D([0], [0], color='#24658a', alpha=0.55, lw=count / max_pair * 10,
                  label=f'{count} forward passes between pair') for count in [3, 10]]
fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.12),
           ncol=2, frameon=False, handlelength=3, columnspacing=3)
fig.text(0.5, 0.045,
         'Circle area: completed forward passes made · Positions: average forward-pass starts and receptions\n'
         'Links: 3+ forward passes per pair, both directions combined; lines are not actual pass paths\n'
         'Any increase in x qualifies; this is not a progressive-pass metric · Source: StatsBomb Open Data',
         ha='center', fontsize=9)
(ROOT / 'figures').mkdir(exist_ok=True)
(ROOT / 'data').mkdir(exist_ok=True)
fig.savefig(ROOT / 'figures' / '09_england_forward_passing_network.png', dpi=180, bbox_inches='tight')
nodes.to_csv(ROOT / 'data' / '04_forward_passing_nodes.csv')
directed.to_csv(ROOT / 'data' / '04_forward_directed_connections.csv', index=False)
pairs.to_csv(ROOT / 'data' / '04_forward_pair_connections.csv', index=False)
plt.show()
