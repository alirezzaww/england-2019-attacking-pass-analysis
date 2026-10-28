# Soccermatics: Using StatsBomb — explore competitions
# https://soccermatics.readthedocs.io/en/latest/gallery/plot_UsingStatsbomb.html

from mplsoccer import Sbopen

# Create the StatsBomb data loader.
parser = Sbopen()

# Load available competition editions as a pandas DataFrame.
competitions = parser.competition()

# Display a small, readable preview.
columns = ['competition_name', 'season_name', 'competition_id', 'season_id']
print(competitions[columns].head().to_string(index=False))
print(f'\nLoaded {len(competitions)} competition editions.')
# In Spyder's Variable Explorer, double-click competitions to see the full table.

# Load matches from the 2019 Women's World Cup (Soccermatics example).
matches = parser.match(competition_id=72, season_id=30)

# Each row is one match. Show its ID, teams, and final score.
match_columns = ['match_id', 'home_team_name', 'away_team_name',
                 'home_score', 'away_score']
print('\n2019 Women\'s World Cup — first five matches:')
print(matches[match_columns].head().to_string(index=False))
print(f'\nLoaded {len(matches)} matches.')
# Double-click matches in Variable Explorer to inspect the full table.

# Load recorded actions from England vs Sweden (match 69301).
events, related, freeze, tactics = parser.event(69301)

# Preview when actions happened, their type, player, and team.
event_columns = ['minute', 'type_name', 'player_name', 'team_name']
print('\nFirst ten match events:')
print(events[event_columns].head(10).to_string(index=False))

# Count how many times each event type occurs across both teams.
event_counts = events['type_name'].value_counts()
print('\nEvent counts — both teams:')
print(event_counts.to_string())
print(f'\nTotal recorded events: {len(events)}')
print(f"Shot events: {event_counts.get('Shot', 0)}")

# Count all recorded events associated with each team (not just shots).
team_event_counts = events['team_name'].value_counts()
print('\nRecorded events by team:')
print(team_event_counts.to_string())

# Keep only shots, then count shot attempts for each team.
is_shot = events['type_name'] == 'Shot'
shots = events[is_shot].copy()
shots_by_team = shots['team_name'].value_counts()
print('\nShot attempts by team:')
print(shots_by_team.to_string())
print(f'Total shots: {len(shots)}')

# Inspect each attempt before interpreting team totals.
shot_details = shots[['minute', 'player_name', 'team_name', 'outcome_name']].copy()
print('\nShot-by-shot record:')
print(shot_details.to_string(index=False))

# A goal is a shot whose recorded outcome equals Goal.
goals = shots[shots['outcome_name'] == 'Goal'].copy()
goals_by_team = goals['team_name'].value_counts().reindex(shots_by_team.index, fill_value=0)
print('\nGoals from shot events by team:')
print(goals_by_team.to_string())
print('\nScorers:')
print(goals[['minute', 'player_name', 'team_name']].to_string(index=False))
# Own goals are separate event types; these counts describe shot goals.

# Sum StatsBomb's supplied shot probabilities separately for each team.
assert shots['shot_statsbomb_xg'].notna().all(), 'Some shots have missing xG.'
assert shots['shot_statsbomb_xg'].between(0, 1).all(), 'Invalid shot probability.'
xg_by_team = shots.groupby('team_name')['shot_statsbomb_xg'].sum()
print('\nTotal expected goals by team (StatsBomb):')
print(xg_by_team.round(3).to_string())
# Round only the display; retain full precision in xg_by_team.

# Average chance quality: total xG divided by number of shots.
xg_per_shot = xg_by_team / shots_by_team
print('\nAverage xG per shot by team:')
print(xg_per_shot.round(3).to_string())

# Player shooting totals: one row per team and player who attempted a shot.
player_shooting = shots.groupby(['team_name', 'player_name']).agg(
    shot_count=('id', 'size'),
    total_xg=('shot_statsbomb_xg', 'sum')
)
print('\nPlayers ranked by shot count (then total xG):')
print(player_shooting.sort_values(['shot_count', 'total_xg'], ascending=False).round(3).to_string())
print('\nPlayers ranked by accumulated xG:')
print(player_shooting.sort_values('total_xg', ascending=False).round(3).to_string())
# These are single-match totals for shooters, not a complete player evaluation.

# Lesson: show England shot coordinates and plot their locations.
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

england_shots = shots[shots['team_name'] == "England Women's"].copy()
print('\nEngland shot locations (StatsBomb coordinates):')
print(england_shots[['player_name', 'x', 'y', 'outcome_name']].to_string(index=False))
assert england_shots[['x', 'y']].notna().all().all()
assert england_shots['x'].between(60, 120).all(), 'Use a full pitch if a shot is outside this half.'
assert england_shots['y'].between(0, 80).all()
england_goals = england_shots[england_shots['outcome_name'] == 'Goal']
england_other_shots = england_shots[england_shots['outcome_name'] != 'Goal']

# VerticalPitch rotates the display: the attacking goal appears at the top.
pitch = VerticalPitch(pitch_type='statsbomb', half=True, line_color='#687078')
fig, ax = pitch.draw(figsize=(8, 7))
pitch.scatter(england_other_shots['x'], england_other_shots['y'], ax=ax,
              s=110, marker='o', facecolors='none', edgecolors='#24658a', linewidths=2, label='Non-goal')
pitch.scatter(england_goals['x'], england_goals['y'], ax=ax,
              s=110, marker='D', color='#c28a19', edgecolors='black', label='Goal')
ax.set_title('England shots against Sweden\n2019 Women’s World Cup · 6 July 2019', fontsize=15, pad=18)
ax.legend(loc='lower left', frameon=False)
fig.text(0.5, 0.02, '11 attempts · Equal-sized markers · Source: StatsBomb Open Data', ha='center', fontsize=10)
fig.subplots_adjust(bottom=0.09, top=0.86)
figure_path = Path(__file__).resolve().parent / 'figures' / '02_england_shot_locations.png'
fig.savefig(figure_path, dpi=180, bbox_inches='tight')
plt.show()
print('Saved shot map:', figure_path)

# Add chance quality: marker area is proportional to StatsBomb xG.
AREA_SCALE = 1800
xg_pitch = VerticalPitch(pitch_type='statsbomb', half=True, line_color='#687078')
xg_fig, xg_ax = xg_pitch.draw(figsize=(8, 8))
xg_fig.set_layout_engine(None)
xg_fig.subplots_adjust(top=0.82, bottom=0.22)
xg_pitch.scatter(england_other_shots['x'], england_other_shots['y'], ax=xg_ax,
                 s=england_other_shots['shot_statsbomb_xg'] * AREA_SCALE,
                 marker='o', facecolors='none', edgecolors='#24658a', linewidths=1.8, label='Non-goal', zorder=3)
xg_pitch.scatter(england_goals['x'], england_goals['y'], ax=xg_ax,
                 s=england_goals['shot_statsbomb_xg'] * AREA_SCALE,
                 marker='D', color='#c28a19', edgecolors='black', label='Goal', zorder=4)
xg_fig.suptitle('England shots against Sweden', fontsize=19, fontweight='bold', y=0.97)
xg_fig.text(0.5, 0.89, f"2019 Women's World Cup · 6 July 2019\n{len(england_shots)} shots · {len(england_goals)} goal · {england_shots.shot_statsbomb_xg.sum():.2f} xG", ha='center', fontsize=11)
xg_ax.legend(loc='lower left', frameon=False)
size_handles = [xg_ax.scatter([], [], s=value * AREA_SCALE, facecolors='none', edgecolors='#24658a', label=f'{value:.2f} xG') for value in [0.05, 0.10, 0.20]]
xg_fig.legend(handles=size_handles, loc='lower center', bbox_to_anchor=(0.5, 0.08), ncol=3, frameon=False)
xg_fig.text(0.5, 0.035, 'Marker area proportional to xG · Source: StatsBomb Open Data · Match 69301', ha='center', fontsize=9)
xg_figure_path = Path(__file__).resolve().parent / 'figures' / '03_england_xg_shot_map.png'
xg_fig.savefig(xg_figure_path, dpi=180, bbox_inches='tight')
plt.show()
print('Saved xG shot map:', xg_figure_path)
print('England goal xG:')
print(england_goals[['player_name', 'shot_statsbomb_xg']].round(3).to_string(index=False))
print('England highest-xG attempt:')
print(england_shots.sort_values('shot_statsbomb_xg', ascending=False)[['player_name', 'outcome_name', 'shot_statsbomb_xg']].head(1).round(3).to_string(index=False))

# Passing lesson 1: count pass attempts, including unsuccessful passes.
passes = events[events['type_name'] == 'Pass'].copy()
passes_by_team = passes['team_name'].value_counts()
print('\nPass attempts by team:')
print(passes_by_team.to_string())
print(f'Total pass attempts: {len(passes)}')
assert passes_by_team.sum() == len(passes)
assert len(passes) == event_counts['Pass']

# Passing lesson 2: StatsBomb leaves outcome_name empty for completed passes.
# This rule applies to pass rows, not to every event type.
print('\nPass outcomes (empty means completed):')
print(passes['outcome_name'].value_counts(dropna=False).to_string())
passes['is_complete'] = passes['outcome_name'].isna()
pass_summary = passes.groupby('team_name').agg(
    attempted=('id', 'size'),
    completed=('is_complete', 'sum')
)
pass_summary['not_completed'] = pass_summary['attempted'] - pass_summary['completed']
pass_summary['completion_pct'] = 100 * pass_summary['completed'] / pass_summary['attempted']
print('\nPass completion by team — all pass events, including throw-ins:')
print(pass_summary.round(1).to_string())
assert (pass_summary['completed'] + pass_summary['not_completed']).equals(pass_summary['attempted'])
assert pass_summary['completion_pct'].between(0, 100).all()
# Not completed groups all named outcomes; inspect unknown outcomes before treating all as failures.
