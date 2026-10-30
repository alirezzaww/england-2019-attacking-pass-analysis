"""Lesson 20: compare passing involvement within the same starting third.

This descriptive extension uses the existing 15-second / shot-xG > 0.10 selection.
The denominator is eligible COMPLETED passes starting in each third, not attempts.
Run in Spyder or a terminal after lesson 13 has created the raw event cache.
"""
from collections import Counter
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZONES = ('Defensive third', 'Middle third', 'Attacking third')
RESTARTS = {'Throw-in', 'Corner', 'Free Kick', 'Kick Off', 'Goal Kick'}
FOCUS = ('Francesca Kirby', 'Lucy Bronze')


def starting_third(x):
    """Assign StatsBomb x in [0, 120]; boundaries 40 and 80 belong forward."""
    if not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 120:
        raise ValueError('Pass-start x must be a finite coordinate from 0 to 120')
    return ZONES[0] if x < 40 else ZONES[1] if x < 80 else ZONES[2]


def summarize(passes, players):
    """Return per-player zone counts; an empty denominator produces None, not 0%."""
    denominator = Counter((p['player_id'], p['zone']) for p in passes)
    numerator = Counter((p['player_id'], p['zone']) for p in passes if p['qualifying'])
    rows = []
    for player in players:
        by_zone = []
        total = sum(denominator[(player['player_id'], zone)] for zone in ZONES)
        for zone in ZONES:
            n = denominator[(player['player_id'], zone)]
            k = numerator[(player['player_id'], zone)]
            by_zone.append({'zone': zone, 'eligible_completed_passes': n, 'qualifying_passes': k,
                            'qualifying_share_pct': 100 * k / n if n else None,
                            'pass_start_mix_pct': 100 * n / total if total else None})
        selected = sum(row['qualifying_passes'] for row in by_zone)
        rows.append({'player_id': player['player_id'], 'player_name': player['player_name'],
                     'eligible_completed_passes': total, 'qualifying_passes': selected,
                     'overall_qualifying_share_pct': 100 * selected / total if total else None,
                     'zones': by_zone})
    return rows


def build_evidence():
    source = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())
    baseline = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
    selected_ids = {(p['match_id'], p['id']) for p in source['selected_passes']['0.10']}
    ledger = []
    for match_id in baseline['match_ids']:
        path = ROOT / f'data/cache_2019_events/{match_id}.json'
        if not path.is_file():
            raise FileNotFoundError(f'Missing {path.name}. Run lesson 13 to create the raw cache.')
        for event in json.loads(path.read_text()):
            if (event['team']['name'] != "England Women's" or event['type']['name'] != 'Pass'
                    or 'outcome' in event['pass']
                    or event['possession_team']['id'] != event['team']['id']
                    or event['pass'].get('type', {}).get('name') in RESTARTS):
                continue
            x = event['location'][0]
            ledger.append({'match_id': match_id, 'id': event['id'], 'player_id': event['player']['id'],
                           'x': x, 'zone': starting_third(x),
                           'qualifying': (match_id, event['id']) in selected_ids})
    assert len({(p['match_id'], p['id']) for p in ledger}) == len(ledger)
    assert {(p['match_id'], p['id']) for p in ledger if p['qualifying']} == selected_ids
    volume = json.loads((ROOT / 'data/17_passing_volume_evidence.json').read_text())
    assert len(ledger) == volume['eligible_passes_total'] == 2837
    players = summarize(ledger, source['players'])
    for player, previous in zip(players, volume['players']):
        assert player['player_id'] == previous['player_id']
        assert player['eligible_completed_passes'] == previous['eligible_completed_passes']
        assert player['qualifying_passes'] == previous['qualifying_passes']
    return {'match_ids': baseline['match_ids'], 'windows_seconds_inclusive': 15,
            'xg_threshold_strictly_greater_than': 0.10,
            'zones': [{'name': name, 'lower_x_inclusive': lower, 'upper_x': upper,
                       'upper_inclusive': upper == 120}
                      for name, lower, upper in zip(ZONES, [0, 40, 80], [40, 80, 120])],
            'denominator_definition': 'Completed possession-team passes starting in the same third; listed restarts excluded',
            'eligible_completed_passes': len(ledger), 'qualifying_passes': len(selected_ids),
            'focus_players': list(FOCUS), 'players': players, 'passes': ledger}


def plot_comparison(evidence):
    # Imported here so the pure selection/summary functions can be tested without plotting libraries.
    import matplotlib.pyplot as plt
    focus = [next(p for p in evidence['players'] if p['player_name'] == name) for name in FOCUS]
    colors = ['#24658a', '#b77516']
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.76, bottom=0.24, wspace=0.25)
    for i, (player, color) in enumerate(zip(focus, colors)):
        positions = [j + (i - 0.5) * 0.34 for j in range(3)]
        for ax, field in zip(axes, ['pass_start_mix_pct', 'qualifying_share_pct']):
            values = [row[field] for row in player['zones']]
            assert all(value is not None for value in values), 'Focus player needs passes in every zone'
            ax.bar(positions, values, width=0.32, color=color, label=player['player_name'].split()[-1])
        for pos, row in zip(positions, player['zones']):
            axes[0].text(pos, row['pass_start_mix_pct'] + 1.5,
                         f"{row['pass_start_mix_pct']:.1f}%", ha='center', fontsize=9)
            axes[1].text(pos, row['qualifying_share_pct'] + 0.5,
                         f"{row['qualifying_passes']}/{row['eligible_completed_passes']}\n{row['qualifying_share_pct']:.1f}%",
                         ha='center', fontsize=9)
    axes[0].set_title('Where did each player’s completed passes start?')
    axes[0].set_ylabel('Share of that player’s eligible completed passes (%)')
    axes[0].set_ylim(0, 70)
    axes[1].set_title('Within each third: how many preceded a shot?')
    axes[1].set_ylabel('Qualifying / eligible completed passes in that third (%)')
    axes[1].set_ylim(0, 22)
    for ax in axes:
        ax.set_xticks(range(3), ['Defensive\nx < 40', 'Middle\n40 ≤ x < 80', 'Attacking\nx ≥ 80'])
        ax.grid(axis='y', color='#e4e7ea')
        ax.set_axisbelow(True)
        ax.legend(frameon=False)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('Kirby and Bronze: compare the passing context', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, '2019 Women’s World Cup · Seven matches · Same possession, 15 seconds, shot xG > 0.10\nLeft: where passes start · Right: qualifying share conditional on starting third', ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'Labels on right show selected / eligible completed passes; failed passes are excluded from both panels.\nSmall counts, broad zones and different roles limit comparison; these are not completion rates or causal effects.\nSource: StatsBomb Open Data · StatsBomb x runs from 0 to 120', ha='center', fontsize=9)
    path = ROOT / 'figures/23_pass_location_context.png'
    fig.savefig(path, dpi=180, bbox_inches='tight')
    print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/20_pass_location_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print(f"Saved {evidence['eligible_completed_passes']} eligible passes and {evidence['qualifying_passes']} selected passes:", path)
    for player in evidence['players']:
        if player['player_name'] in FOCUS:
            print(player['player_name'])
            for row in player['zones']:
                value = row['qualifying_share_pct']
                text = f'{value:.2f}%' if value is not None else 'undefined'
                print(f"  {row['zone']}: {row['qualifying_passes']}/{row['eligible_completed_passes']} = {text}")
    plot_comparison(evidence)


if __name__ == '__main__':
    main()
