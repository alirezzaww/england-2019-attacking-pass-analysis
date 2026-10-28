# Extra guided practice after Soccermatics' forward passing network challenge.
# Compare forward passing frequency with forward-pass completion rate.
from mplsoccer import Sbopen

events, related, freeze, tactics = Sbopen().event(69301)
TEAM = "England Women's"
first_sub = events[
    (events['type_name'] == 'Substitution') & (events['team_name'] == TEAM)
].sort_values('index').iloc[0]

# Keep attempted passes, including failed passes. Same time window as lesson 04.
attempts = events[
    (events['type_name'] == 'Pass')
    & (events['team_name'] == TEAM)
    & (events['index'] < first_sub['index'])
    & (events['sub_type_name'] != 'Throw-in')
].copy()

# A missing coordinate prevents us from deciding whether a pass was forward.
has_coordinates = attempts[['x', 'end_x']].notna().all(axis=1)
forward_attempts = attempts[has_coordinates & (attempts['end_x'] > attempts['x'])].copy()

# StatsBomb completed passes have a missing (null) outcome_name.
# Explicit Unknown outcomes cannot be treated as known failures.
unknown_outcome = forward_attempts['outcome_name'].eq('Unknown')
assessed_forward = forward_attempts[~unknown_outcome].copy()
assessed_forward['completed'] = assessed_forward['outcome_name'].isna()

summary = assessed_forward.groupby('player_name')['completed'].agg(
    forward_attempts='size', forward_completed='sum'
)
summary['forward_failed'] = summary['forward_attempts'] - summary['forward_completed']
summary['forward_success_pct'] = (
    summary['forward_completed'] / summary['forward_attempts'] * 100
)
assert summary.forward_attempts.sum() == len(assessed_forward)
assert summary.forward_completed.sum() == assessed_forward.completed.sum()
assert summary.forward_success_pct.between(0, 100).all()

print('England vs Sweden, before England\'s first substitution; throw-ins excluded.')
print(f'Pass attempts with missing x/end_x: {(~has_coordinates).sum()}')
print(f'Forward attempts with Unknown outcome excluded: {unknown_outcome.sum()}')
print('\nForward-pass success rate: completed / attempted * 100')
print(summary.sort_values('forward_attempts', ascending=False).round(1).to_string())
print(f'\nTeam: {summary.forward_completed.sum()} completed / '
      f'{summary.forward_attempts.sum()} attempted = '
      f'{summary.forward_completed.sum() / summary.forward_attempts.sum():.1%}')
print('\nLucy Bronze:')
print(summary.loc['Lucy Bronze'].round(1).to_string())
print('\nDifferent question from forward share among completed passes!')
print('Small samples and different player roles limit player comparisons.')
