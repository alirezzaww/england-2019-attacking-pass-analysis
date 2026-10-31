"""Lesson 23: check match overlap before comparing score-state percentages.

Uses saved lesson-22 pre-pass labels. Select common fixtures by positive eligible
completed-pass counts in BOTH states, never by a positive qualifying numerator.
This is a descriptive restriction, not an estimate of a causal score effect.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATES = ('Leading', 'Drawing', 'Trailing')


def state_summary(passes, state):
    """Calculate a pooled ratio; zero exposure is undefined, not measured zero."""
    rows = [p for p in passes if p['state'] == state]
    k, n = sum(p['qualifying'] for p in rows), len(rows)
    return {'state': state, 'qualifying_passes': k, 'eligible_completed_passes': n,
            'qualifying_share_pct': 100 * k / n if n else None}


def compare_states(passes, match_ids, first, second):
    """Compare all fixtures and the subset with observed passes in both states."""
    if first == second or first not in STATES or second not in STATES:
        raise ValueError('Choose two different recognised score states')
    if len(set(match_ids)) != len(match_ids):
        raise ValueError('Fixture IDs must be unique')
    allowed = set(match_ids)
    if any(p['match_id'] not in allowed for p in passes):
        raise ValueError('Passes contain an unexpected fixture')
    first_matches = {p['match_id'] for p in passes if p['state'] == first}
    second_matches = {p['match_id'] for p in passes if p['state'] == second}
    common = [m for m in match_ids if m in first_matches and m in second_matches]
    restricted = [p for p in passes if p['match_id'] in common]
    all_pool = [state_summary(passes, state) for state in [first, second]]
    common_pool = [state_summary(restricted, state) for state in [first, second]]
    def difference(pool):
        shares = [cell['qualifying_share_pct'] for cell in pool]
        return shares[1] - shares[0] if all(value is not None for value in shares) else None
    return {'states': [first, second], 'common_match_ids': common,
            'all_fixture_pool': all_pool, 'common_fixture_pool': common_pool,
            'all_difference_second_minus_first_pp': difference(all_pool),
            'common_difference_second_minus_first_pp': difference(common_pool),
            'per_common_fixture': [
                {'match_id': m, 'states': [state_summary([p for p in passes if p['match_id'] == m], state)
                                         for state in [first, second]]} for m in common]}


def build_evidence():
    source = json.loads((ROOT / 'data/22_score_state_evidence.json').read_text())
    passes, match_ids = source['passes'], source['match_ids']
    audits = {a['match_id']: a for a in source['match_audits']}
    coverage = [{'match_id': m, 'opponent': audits[m]['opponent'],
                 'states': [state_summary([p for p in passes if p['match_id'] == m], state)
                            for state in STATES]} for m in match_ids]
    comparisons = {f'{first.lower()}_vs_{second.lower()}': compare_states(passes, match_ids, first, second)
                   for first, second in [('Drawing', 'Trailing'), ('Leading', 'Trailing')]}
    return {'source': '22_score_state_evidence.json', 'match_ids': match_ids,
            'scope': 'England whole team, all eligible starting locations',
            'time_window_seconds_inclusive': 15, 'xg_threshold_strictly_greater_than': 0.10,
            'common_fixture_rule': 'Positive eligible completed-pass denominator in both states; qualifying numerator may be zero',
            'coverage': coverage, 'comparisons': comparisons,
            'interpretation_limit': 'Restricting to common fixtures changes the analysed sample; game phase, lineup and other context remain uncontrolled'}


def plot_evidence(evidence):
    import numpy as np
    import matplotlib.pyplot as plt
    coverage = evidence['coverage']
    comparison = evidence['comparisons']['drawing_vs_trailing']
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.77, bottom=0.25, wspace=0.45)
    values = np.array([[r['eligible_completed_passes'] for r in m['states']] for m in coverage])
    cmap = plt.get_cmap('Blues').copy(); cmap.set_bad('#ecebe7')
    axes[0].imshow(np.ma.masked_equal(values, 0), cmap=cmap, vmin=0, vmax=400, aspect='auto')
    for i in range(len(coverage)):
        for j in range(3):
            n = values[i, j]
            axes[0].text(j, i, str(n) if n else '—', ha='center', va='center',
                         color='white' if n > 200 else '#172d3b', fontsize=11)
    axes[0].set_xticks(range(3), STATES)
    axes[0].set_yticks(range(7), ['Scotland', 'Argentina', 'Japan', 'Cameroon', 'Norway', 'USA', 'Sweden'])
    axes[0].set_title('Eligible completed passes in each fixture', fontsize=12, pad=12)
    colors = ['#b77516', '#8b537c']
    for j, (state, color) in enumerate(zip(['Drawing', 'Trailing'], colors)):
        positions = [i + (j - 0.5) * 0.34 for i in range(2)]
        cells = [comparison[key][j] for key in ['all_fixture_pool', 'common_fixture_pool']]
        axes[1].bar(positions, [r['qualifying_share_pct'] for r in cells], color=color, width=0.32, label=state)
        for position, cell in zip(positions, cells):
            axes[1].text(position, cell['qualifying_share_pct'] + 0.10,
                         f"{cell['qualifying_passes']}/{cell['eligible_completed_passes']}\n{cell['qualifying_share_pct']:.2f}%",
                         ha='center', fontsize=10)
    axes[1].set_xticks([0, 1], ['All seven fixtures', 'USA + Sweden only'])
    axes[1].set_ylabel('Qualifying / eligible completed passes (%)')
    axes[1].set_ylim(0, 4)
    axes[1].set_title('Drawing versus trailing: the match set matters', fontsize=12, pad=12)
    axes[1].legend(frameon=False, loc='upper right')
    axes[1].grid(axis='y', color='#e4e7ea'); axes[1].set_axisbelow(True)
    for ax in axes:
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('England: check that the match sets overlap', fontsize=21, weight='bold', y=0.96)
    fig.text(0.5, 0.85, '2019 Women’s World Cup · Whole team, all starting locations · Same possession, 15 seconds, shot xG > 0.10\nNo fixture contains eligible passes while both leading and trailing', ha='center', fontsize=11)
    fig.text(0.5, 0.06, 'Left: — means no eligible passes in that state; it is not a measured 0% qualifying share.\nRight: 0/120 is a measured zero for the selected pass definition. Pooled ratios use summed counts.\nRestricting the match set does not isolate a causal score effect · Source: StatsBomb Open Data', ha='center', fontsize=9)
    path = ROOT / 'figures/26_within_match_score_comparison.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/23_within_match_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    for name, comparison in evidence['comparisons'].items():
        print(name, 'common fixtures:', comparison['common_match_ids'])
        for key in ['all_fixture_pool', 'common_fixture_pool']:
            for cell in comparison[key]:
                value = cell['qualifying_share_pct']
                share = f'{value:.2f}%' if value is not None else 'undefined'
                print(f"  {key} {cell['state']}: {cell['qualifying_passes']}/{cell['eligible_completed_passes']} = {share}")
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
