# Soccermatics Pass heat maps: first learn the 15-second rule in ONE match window.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html
# We keep the pre-first-substitution period for continuity with lessons 03-06.
from mplsoccer import Sbopen

events, related, freeze, tactics = Sbopen().event(69301)
TEAM = "England Women's"
first_sub = events[
    (events['type_name'] == 'Substitution') & (events['team_name'] == TEAM)
].sort_values('index').iloc[0]
window = events[
    (events['team_name'] == TEAM) & (events['index'] < first_sub['index'])
].copy()
window['time_seconds'] = window['minute'] * 60 + window['second']

# Begin with the same completed passes as the previous heatmap.
completed_passes = window[
    (window['type_name'] == 'Pass')
    & window['outcome_name'].isna()
    & (window['sub_type_name'] != 'Throw-in')
].copy()

# Match the tutorial's additional filters: possession-team passes, no restarts.
restarts = ['Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick']
passes = completed_passes[
    (completed_passes['possession_team_id'] == completed_passes['team_id'])
    & ~completed_passes['sub_type_name'].isin(restarts)
].copy()
shots = window[window['type_name'] == 'Shot'][
    ['match_id', 'period', 'possession', 'id', 'index', 'time_seconds',
     'minute', 'second', 'player_name', 'shot_statsbomb_xg']
].rename(columns={
    'id': 'shot_id', 'index': 'shot_index', 'time_seconds': 'shot_time_seconds',
    'minute': 'shot_minute', 'second': 'shot_second', 'player_name': 'shooter',
    'shot_statsbomb_xg': 'shot_xg'
})

# Match a pass only with England shots from the same possession and half.
linked = passes.merge(shots, on=['match_id', 'period', 'possession'], how='inner')
linked['seconds_before_shot'] = linked['shot_time_seconds'] - linked['time_seconds']
qualifying = linked[
    (linked['index'] < linked['shot_index'])
    & linked['seconds_before_shot'].between(0, 15)
].copy()

# A pass can precede two shots in a possession: count it ONCE, using the next shot.
danger_passes = qualifying.sort_values(['seconds_before_shot', 'shot_index']).drop_duplicates('id')
danger_passes = danger_passes.sort_values('index').reset_index(drop=True)
assert danger_passes.id.is_unique
assert danger_passes.seconds_before_shot.between(0, 15).all()
assert len(danger_passes) <= len(passes)
print('England vs Sweden — before England\'s first substitution at 49:23.')
print(f'Previous heatmap: {len(completed_passes)} completed passes, excluding throw-ins.')
print(f'Eligible possession-team passes after excluding all listed restarts: {len(passes)}')
print(f'England shots in this window: {len(shots)}')
print(f'Unique passes within 15 seconds before a same-possession England shot: {len(danger_passes)}')
print('\nPass -> next qualifying shot:')
for row in danger_passes.itertuples():
    print(f'Half {int(row.period)}, {int(row.minute):02d}:{int(row.second):02d} {row.player_name} -> '
          f'{int(row.shot_minute):02d}:{int(row.shot_second):02d} {row.shooter} shot '
          f'({int(row.seconds_before_shot)} seconds later)')
print('\nThis is the course\'s time-window definition, not proof a pass caused a shot.')
print('A qualifying pass can be backward or sideways; it need not be the final pass.')
