"""Lesson 22: label each eligible pass by England's score immediately BEFORE it.

Uses the unchanged lesson-20 ledger and checks goal reconstruction against provider
match scores. Counts goals from Shot/Goal or canonical Own Goal Against events;
Own Goal For is not counted again. Shootout events are excluded.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATES = ('Leading', 'Drawing', 'Trailing')
METADATA_URL = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/72/30.json'
METADATA_PATH = ROOT / 'data/cache_2019_events/matches_72_30.json'


def score_state(england_goals, opponent_goals):
    if england_goals > opponent_goals:
        return 'Leading'
    return 'Trailing' if england_goals < opponent_goals else 'Drawing'


def annotate_match(events, passes, england_id, opponent_id):
    """Walk event order, attach pre-event score, and then apply goal updates."""
    scores = {england_id: 0, opponent_id: 0}
    eligible = {p['id']: p for p in passes}
    assert len(eligible) == len(passes), 'Duplicate pass IDs'
    ordered = sorted(events, key=lambda e: e['index'])
    assert len({e['index'] for e in ordered}) == len(ordered), 'Duplicate event indices'
    tagged, goals = [], []
    for event in ordered:
        if event['period'] == 5:
            continue
        if event['id'] in eligible:
            original = eligible[event['id']]
            tagged.append({'match_id': original['match_id'], 'id': original['id'],
                           'player_id': original['player_id'], 'qualifying': original['qualifying'],
                           'index': event['index'], 'england_goals_before': scores[england_id],
                           'opponent_goals_before': scores[opponent_id],
                           'state': score_state(scores[england_id], scores[opponent_id])})
        kind = event['type']['name']
        credited = None
        if kind == 'Shot' and event['shot']['outcome']['name'] == 'Goal':
            credited = event['team']['id']
        elif kind == 'Own Goal Against':
            conceding = event['team']['id']
            assert conceding in scores
            credited = opponent_id if conceding == england_id else england_id
        if credited is not None:
            assert credited in scores, 'Goal credited to an unexpected team'
            before = [scores[england_id], scores[opponent_id]]
            scores[credited] += 1
            goals.append({'id': event['id'], 'index': event['index'], 'type': kind,
                          'credited_team_id': credited, 'score_before': before,
                          'score_after': [scores[england_id], scores[opponent_id]]})
    assert {p['id'] for p in tagged} == set(eligible), 'An eligible pass was not tagged'
    return tagged, goals, [scores[england_id], scores[opponent_id]]


def summarize(rows):
    """Return selected / eligible completed-pass shares, not completion rates."""
    totals = Counter(p['state'] for p in rows)
    selected = Counter(p['state'] for p in rows if p['qualifying'])
    return [{'state': state, 'eligible_completed_passes': totals[state],
             'qualifying_passes': selected[state],
             'qualifying_share_pct': 100 * selected[state] / totals[state] if totals[state] else None}
            for state in STATES]


def build_evidence():
    context = json.loads((ROOT / 'data/20_pass_location_evidence.json').read_text())
    if not METADATA_PATH.is_file():
        import requests
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(METADATA_URL, timeout=60)
        response.raise_for_status()
        response.json()
        METADATA_PATH.write_bytes(response.content)
    metadata = {m['match_id']: m for m in json.loads(METADATA_PATH.read_text())}
    ledger, audits = [], []
    for match_id in context['match_ids']:
        match = metadata[match_id]
        home, away = match['home_team'], match['away_team']
        england_home = home['home_team_name'] == "England Women's"
        assert england_home or away['away_team_name'] == "England Women's"
        england_id = home['home_team_id'] if england_home else away['away_team_id']
        opponent_id = away['away_team_id'] if england_home else home['home_team_id']
        opponent = away['away_team_name'] if england_home else home['home_team_name']
        expected = [match['home_score'], match['away_score']] if england_home else [match['away_score'], match['home_score']]
        events = json.loads((ROOT / f'data/cache_2019_events/{match_id}.json').read_text())
        passes = [p for p in context['passes'] if p['match_id'] == match_id]
        tagged, goals, final = annotate_match(events, passes, england_id, opponent_id)
        assert final == expected, f'Reconstructed score disagrees with provider metadata for {match_id}'
        ledger.extend(tagged)
        audits.append({'match_id': match_id, 'opponent': opponent, 'match_date': match['match_date'],
                       'england_team_id': england_id, 'opponent_team_id': opponent_id,
                       'provider_final_score_england_opponent': expected,
                       'reconstructed_final_score_england_opponent': final,
                       'goals': goals, 'states': summarize(tagged)})
    assert len(ledger) == context['eligible_completed_passes'] == 2837
    assert sum(p['qualifying'] for p in ledger) == context['qualifying_passes'] == 98
    players = [{ 'player_id': player['player_id'], 'player_name': player['player_name'],
                 'states': summarize([p for p in ledger if p['player_id'] == player['player_id']])}
               for player in context['players']]
    return {'match_ids': context['match_ids'], 'time_window_seconds_inclusive': 15,
            'xg_threshold_strictly_greater_than': 0.10, 'state_time': 'Immediately before the pass by event index',
            'own_goal_rule': 'Count Own Goal Against once for the opponent; ignore Own Goal For counterpart',
            'metadata_source': {'url': METADATA_URL, 'relative_path': str(METADATA_PATH.relative_to(ROOT)),
                                'sha256': hashlib.sha256(METADATA_PATH.read_bytes()).hexdigest()},
            'match_audits': audits, 'team_states': summarize(ledger), 'players': players, 'passes': ledger}


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    rows = evidence['team_states']
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.76, bottom=0.25, wspace=0.25)
    colors = ['#24658a', '#b77516', '#8b537c']
    axes[0].bar(STATES, [r['qualifying_passes'] for r in rows], color=colors, width=0.55)
    axes[1].bar(STATES, [r['qualifying_share_pct'] for r in rows], color=colors, width=0.55)
    for j, row in enumerate(rows):
        axes[0].text(j, row['qualifying_passes'] + 1, str(row['qualifying_passes']), ha='center')
        axes[1].text(j, row['qualifying_share_pct'] + 0.12,
                     f"{row['qualifying_passes']}/{row['eligible_completed_passes']}\n{row['qualifying_share_pct']:.2f}%", ha='center')
    axes[0].set_ylim(0, 85)
    axes[0].set_ylabel('Qualifying passes (count)')
    axes[0].set_title('How many passes qualified?')
    axes[1].set_ylim(0, 6)
    axes[1].set_ylabel('Qualifying / eligible completed passes in that state (%)')
    axes[1].set_title('What share qualified within each score state?')
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea'); ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('England: passing involvement by score state', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, '2019 Women’s World Cup · Seven fixtures · State immediately BEFORE each pass\nSame possession, 15 seconds, shot xG > 0.10 · Same completed-pass filters throughout', ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'All eligible starting locations included · Counts and percentages answer different questions.\nTrailing passes occur only against USA and Sweden; score state is mixed with opponent, match phase and lineup.\nDescriptive association, not a causal effect of leading or trailing · Source: StatsBomb Open Data', ha='center', fontsize=9)
    path = ROOT / 'figures/25_score_state_context.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/22_score_state_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    for row in evidence['team_states']:
        print(f"{row['state']}: {row['qualifying_passes']}/{row['eligible_completed_passes']} = {row['qualifying_share_pct']:.2f}%")
    print('All seven reconstructed final scores match provider metadata.')
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
