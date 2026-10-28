# Soccermatics: Passing Networks — step 1, count player-to-player connections.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html
from pathlib import Path
from mplsoccer import Sbopen

parser = Sbopen()
events, related, freeze, tactics = parser.event(69301)
TEAM = "England Women's"

# The course uses the period before England's first substitution.
# Use StatsBomb's explicit event index, not pandas' row labels.
substitutions = events[
    (events['type_name'] == 'Substitution') & (events['team_name'] == TEAM)
].sort_values('index')
assert not substitutions.empty, 'This example expects a substitution.'
first_substitution = substitutions.iloc[0]
cutoff_index = first_substitution['index']

# A connection must be a completed England pass before the cutoff, not a throw-in.
network_passes = events[
    (events['type_name'] == 'Pass')
    & (events['team_name'] == TEAM)
    & (events['index'] < cutoff_index)
    & (events['outcome_name'].isna())
    & (events['sub_type_name'] != 'Throw-in')
].copy()
assert not network_passes.empty
assert network_passes[['player_name', 'pass_recipient_name']].notna().all().all()

# Keep direction for this first step: Bronze -> Scott differs from Scott -> Bronze.
connections = network_passes.groupby(
    ['player_name', 'pass_recipient_name']
).size().reset_index(name='pass_count')
connections = connections.sort_values(
    ['pass_count', 'player_name', 'pass_recipient_name'],
    ascending=[False, True, True]
).reset_index(drop=True)

print(f"England vs Sweden: first England substitution at {int(first_substitution['minute'])}:{int(first_substitution['second']):02d}")
print(f'Completed England passes before that substitution, excluding throw-ins: {len(network_passes)}')
print('\nTop ten directed passing connections (passer -> recipient):')
print(connections.head(10).to_string(index=False))
assert connections['pass_count'].sum() == len(network_passes)

output_path = Path(__file__).resolve().parent / 'data' / '03_directed_pass_connections.csv'
output_path.parent.mkdir(exist_ok=True)
connections.to_csv(output_path, index=False)
print('\nSaved:', output_path)
# The course later combines both directions into an undirected network edge.
# This restricted time window differs from the previous full-match player counts.
# Connection counts measure frequency, not danger or a player's overall ability.

# Step 2: average the locations where each player passed and received the ball.
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch

pass_starts = network_passes[['player_name', 'x', 'y']].copy()
pass_ends = network_passes[['pass_recipient_name', 'end_x', 'end_y']].rename(
    columns={'pass_recipient_name': 'player_name', 'end_x': 'x', 'end_y': 'y'}
)
involvements = pd.concat([pass_starts, pass_ends], ignore_index=True)
assert involvements[['x', 'y']].notna().all().all()
player_nodes = involvements.groupby('player_name')[['x', 'y']].mean()
player_nodes['passes_made'] = network_passes.groupby('player_name').size().reindex(player_nodes.index, fill_value=0)
player_nodes['passes_received'] = network_passes.groupby('pass_recipient_name').size().reindex(player_nodes.index, fill_value=0)
player_nodes['marker_area'] = player_nodes['passes_made'] / player_nodes['passes_made'].max() * 1600
assert len(involvements) == 2 * len(network_passes)
assert player_nodes['passes_made'].sum() == len(network_passes)
assert player_nodes['passes_received'].sum() == len(network_passes)
assert player_nodes['x'].between(0, 120).all() and player_nodes['y'].between(0, 80).all()
print('\nPlayer nodes — average pass and reception locations:')
print(player_nodes[['x', 'y', 'passes_made', 'passes_received']].round(1).to_string())

pitch = Pitch(pitch_type='statsbomb', line_color='#687078')
node_fig, node_ax = pitch.draw(figsize=(12, 8))
node_fig.set_layout_engine(None)
node_fig.subplots_adjust(top=0.80, bottom=0.19)
pitch.scatter(player_nodes['x'], player_nodes['y'], s=player_nodes['marker_area'],
              color='#24658a', edgecolors='white', linewidths=1.5, alpha=0.85, ax=node_ax, zorder=3)
for name, node in player_nodes.iterrows():
    pitch.annotate(name.split()[-1], xy=(node['x'], node['y']), xytext=(0, 20),
                   textcoords='offset points', ha='center', fontsize=11, ax=node_ax, zorder=4)
title_text = node_fig.suptitle('England: average passing involvement locations', fontsize=20, fontweight='bold', y=0.96)
subtitle_text = node_fig.text(0.5, 0.875,
              f"Against Sweden · 6 July 2019 · Before England’s first substitution ({int(first_substitution['minute'])}:{int(first_substitution['second']):02d})\nCompleted passes only · Throw-ins excluded · Attack →",
              ha='center', fontsize=11)
legend_handles = [node_ax.scatter([], [], s=count / player_nodes['passes_made'].max() * 1600,
                                  color='#24658a', alpha=0.85, label=f'{count} passes made') for count in [10, 20, 30]]
node_fig.legend(handles=legend_handles, loc='lower center', bbox_to_anchor=(0.5, 0.065),
                 ncol=3, frameon=False, columnspacing=2.5, handlelength=3, handletextpad=1.8)
footer_text = node_fig.text(0.5, 0.025,
              'Positions: mean of pass starts and receptions, not tracking · Circle area: completed passes made\nSource: StatsBomb Open Data',
              ha='center', fontsize=9)
node_path = Path(__file__).resolve().parent / 'figures' / '06_england_passing_nodes.png'
node_path.parent.mkdir(exist_ok=True)
node_fig.savefig(node_path, dpi=180, bbox_inches='tight')
player_nodes.to_csv(output_path.parent / '03_passing_nodes.csv')
print('\nSaved:', node_path)
# These positions describe selected on-ball involvements, not a measured formation.

# Step 3: combine both directions, then draw the player-to-player connections.
# Sorting gives A -> B and B -> A the same pair, without changing the raw passes.
pair_counts = connections.copy()
pair_counts[['player_1', 'player_2']] = pd.DataFrame(
    [sorted([row.player_name, row.pass_recipient_name])
     for row in connections.itertuples()], index=connections.index
)
pair_counts = pair_counts.groupby(['player_1', 'player_2'])['pass_count'].sum().reset_index()
pair_counts = pair_counts.sort_values('pass_count', ascending=False).reset_index(drop=True)
assert pair_counts['pass_count'].sum() == len(network_passes)
assert not pair_counts.duplicated(['player_1', 'player_2']).any()
assert (pair_counts['player_1'] != pair_counts['player_2']).all()
pair_counts.to_csv(output_path.parent / '03_undirected_pass_connections.csv', index=False)

# Match the tutorial code: > 2 means a minimum of THREE passes combined.
MIN_PAIR_PASSES = 3
visible_connections = pair_counts[pair_counts['pass_count'] >= MIN_PAIR_PASSES].copy()
assert not visible_connections.empty
max_pair_passes = visible_connections['pass_count'].max()
for connection in visible_connections.itertuples():
    player_1 = player_nodes.loc[connection.player_1]
    player_2 = player_nodes.loc[connection.player_2]
    line_width = connection.pass_count / max_pair_passes * 10
    pitch.lines(player_1['x'], player_1['y'], player_2['x'], player_2['y'],
                lw=line_width, color='#24658a', alpha=0.55, zorder=2, ax=node_ax)

# Reuse the node plot; the previous circles-only image has already been saved.
title_text.set_text('England: passing network against Sweden')
subtitle_text.set_text(
    f"6 July 2019 · Before England’s first substitution ({int(first_substitution['minute'])}:{int(first_substitution['second']):02d})\n"
    f"Completed passes · Throw-ins excluded · Links: {MIN_PAIR_PASSES}+ passes in both directions combined · Attack →"
)
footer_text.set_text(
    'Circle area: completed passes made · Locations: average pass starts and receptions\n'
    'Lines connect player averages, not actual pass paths · Source: StatsBomb Open Data'
)
from matplotlib.lines import Line2D
line_handles = [Line2D([0], [0], color='#24658a', alpha=0.55,
                       lw=count / max_pair_passes * 10, label=f'{count} exchanged')
                for count in [5, 10, 20]]
node_fig.legend(handles=line_handles, loc='lower center', bbox_to_anchor=(0.5, 0.13),
                ncol=3, frameon=False, handlelength=3, columnspacing=2.5)
network_path = node_path.parent / '07_england_passing_network.png'
node_fig.savefig(network_path, dpi=180, bbox_inches='tight')

# A labelled teaching copy makes one connection's exact count explicit.
bronze = player_nodes.loc['Lucy Bronze']
parris = player_nodes.loc['Nikita Parris']
bronze_to_parris = int(connections.loc[
    (connections.player_name == 'Lucy Bronze')
    & (connections.pass_recipient_name == 'Nikita Parris'), 'pass_count'].sum())
parris_to_bronze = int(connections.loc[
    (connections.player_name == 'Nikita Parris')
    & (connections.pass_recipient_name == 'Lucy Bronze'), 'pass_count'].sum())
pitch.annotate(
    f'{bronze_to_parris + parris_to_bronze} passes total\n'
    f'Bronze → Parris: {bronze_to_parris} | Parris → Bronze: {parris_to_bronze}',
    xy=((bronze.x + parris.x) / 2, (bronze.y + parris.y) / 2),
    xytext=(85, 77), ha='center', va='center', fontsize=9, color='#123e58',
    bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#24658a'),
    arrowprops=dict(arrowstyle='->', color='#123e58', lw=1.8),
    ax=node_ax, zorder=6
)
node_fig.savefig(node_path.parent / '08_bronze_parris_connection_explained.png',
                 dpi=180, bbox_inches='tight')
print('\nTop ten connections, both directions combined:')
print(pair_counts.head(10).to_string(index=False))
print(f'Plotted {len(visible_connections)} of {len(pair_counts)} pairs; '
      f'{visible_connections.pass_count.sum()} of {len(network_passes)} passes represented by lines.')
print('\nSaved:', network_path)

# Step 4: the course's centralisation score uses passes MADE by each player.
# Use all selected passes, including pairs hidden by the line-display threshold.
passes_by_player = player_nodes['passes_made'].sort_values(ascending=False)
player_count = len(passes_by_player)
total_passes = passes_by_player.sum()
most_passes = passes_by_player.max()
gaps_from_leader = most_passes - passes_by_player
assert player_count > 1 and total_passes > 0
centralisation = gaps_from_leader.sum() / ((player_count - 1) * total_passes)
assert 0 <= centralisation <= 1
print('\nCompleted passes MADE by each player:')
print(passes_by_player.to_string())
print(f'Average per player: {total_passes / player_count:.1f}')
print(f'Centralisation: {centralisation:.3f}')
print('0 = equal pass counts; higher = counts are more concentrated.')
print('This describes passing volume, not passing quality or match performance.')
plt.show()
