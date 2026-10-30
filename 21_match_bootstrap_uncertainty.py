"""Lesson 21: paired whole-match bootstrap of attacking-third qualifying share.

Educational percentile bootstrap; seven selected matches do not support a reliable
population interval. Extends lesson 20 without changing pass or shot definitions.
Primary method reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
Uses Python's standard-library RNG so saved evidence can be checked without NumPy.
"""
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
PLAYERS = ('Francesca Kirby', 'Lucy Bronze')
N_RESAMPLES = 10000
SEED = 20261030


def pooled_share(rows, indices, player_index):
    """Pool numerator and denominator together, preserving zero-exposure fixtures."""
    numerator = sum(rows[i]['players'][player_index]['qualifying_passes'] for i in indices)
    denominator = sum(rows[i]['players'][player_index]['eligible_completed_passes'] for i in indices)
    return 100 * numerator / denominator if denominator else None


def percentile(values, q):
    """Linear-interpolated empirical quantile (q in [0, 1])."""
    if not values or not 0 <= q <= 1:
        raise ValueError('Provide nonempty values and a quantile between 0 and 1')
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def paired_bootstrap(rows, n_resamples=N_RESAMPLES, seed=SEED):
    """Draw the same fixture indices for both players, with replacement."""
    if not rows or n_resamples < 1:
        raise ValueError('Provide match rows and a positive number of resamples')
    rng = random.Random(seed)
    differences, invalid = [], 0
    example = None
    for _ in range(n_resamples):
        indices = [rng.randrange(len(rows)) for _ in rows]
        if example is None:
            example = indices
        first = pooled_share(rows, indices, 0)
        second = pooled_share(rows, indices, 1)
        if first is None or second is None:
            invalid += 1
        else:
            differences.append(first - second)
    return differences, invalid, example


def build_evidence():
    context = json.loads((ROOT / 'data/20_pass_location_evidence.json').read_text())
    players = [next(p for p in context['players'] if p['player_name'] == name) for name in PLAYERS]
    rows = []
    for match_id in context['match_ids']:
        counts = []
        for player in players:
            passes = [p for p in context['passes'] if p['match_id'] == match_id
                      and p['player_id'] == player['player_id'] and p['zone'] == 'Attacking third']
            counts.append({'qualifying_passes': sum(p['qualifying'] for p in passes),
                           'eligible_completed_passes': len(passes)})
        rows.append({'match_id': match_id, 'players': counts})
    observed = [pooled_share(rows, list(range(len(rows))), j) for j in range(2)]
    differences, invalid, example = paired_bootstrap(rows)
    if not differences:
        raise ValueError('No resample has positive exposure for both players')
    interval = [percentile(differences, q) for q in [0.025, 0.975]]
    return {
        'source': '20_pass_location_evidence.json', 'zone': 'Attacking third',
        'xg_threshold_strictly_greater_than': 0.10, 'time_window_seconds_inclusive': 15,
        'player_order': [{'player_id': p['player_id'], 'player_name': p['player_name']} for p in players],
        'match_counts': rows, 'observed_shares_pct': observed,
        'observed_difference_percentage_points': observed[0] - observed[1],
        'method': 'Paired whole-match bootstrap with replacement; pooled ratios; percentile interval',
        'n_resamples': N_RESAMPLES, 'seed': SEED, 'random_generator': 'Python random.Random.randrange',
        'valid_resamples': len(differences), 'zero_denominator_resamples': invalid,
        'example_match_ids': [rows[i]['match_id'] for i in example],
        'percentiles': [0.025, 0.975], 'percentile_method': 'linear interpolation at (n - 1) * q',
        'illustrative_interval_percentage_points': interval,
        'differences_percentage_points': differences,
        'interpretation_limit': 'Only seven selected, nonexchangeable tournament fixtures; no validated population coverage, p-value or player-quality claim',
    }


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.76, bottom=0.25, wspace=0.27)
    axes[0].bar(['Kirby', 'Bronze'], evidence['observed_shares_pct'], color=['#24658a', '#b77516'], width=0.55)
    for j, share in enumerate(evidence['observed_shares_pct']):
        k = sum(r['players'][j]['qualifying_passes'] for r in evidence['match_counts'])
        n = sum(r['players'][j]['eligible_completed_passes'] for r in evidence['match_counts'])
        axes[0].text(j, share + 0.6, f'{k}/{n}\n{share:.1f}%', ha='center')
    axes[0].set_ylim(0, 22)
    axes[0].set_ylabel('Qualifying / eligible completed passes (%)')
    axes[0].set_title('Observed attacking-third shares')
    lower, upper = evidence['illustrative_interval_percentage_points']
    observed = evidence['observed_difference_percentage_points']
    axes[1].hist(evidence['differences_percentage_points'], bins=35, color='#24658a', alpha=0.8)
    axes[1].axvspan(lower, upper, color='#b77516', alpha=0.13, label='Central 95% of valid resamples')
    axes[1].axvline(0, color='#172d3b', linewidth=1.5, label='Zero = equal shares')
    axes[1].axvline(observed, color='#b77516', linewidth=2, linestyle='--', label=f'Observed: {observed:.2f} pp')
    axes[1].set_xlabel('Kirby minus Bronze (percentage points)')
    axes[1].set_ylabel('Number of resamples')
    axes[1].set_title(f'Illustrative percentile interval: {lower:.2f} to {upper:.2f} pp')
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea')
        ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('Kirby–Bronze: match-sample uncertainty', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, '2019 Women’s World Cup · Seven fixtures · Attacking-third starts only\nSame possession, 15 seconds, shot xG > 0.10 · Both players use the same resampled matches', ha='center', fontsize=11)
    fig.text(0.5, 0.055, '10,000 seven-match draws with replacement · Seed 20261030 · Whole-match counts stay together\nOnly seven selected fixtures; this teaching interval has no validated population coverage.\nNot a p-value, probability of superiority or causal effect · Source: StatsBomb Open Data', ha='center', fontsize=9)
    path = ROOT / 'figures/24_match_bootstrap_uncertainty.png'
    fig.savefig(path, dpi=180, bbox_inches='tight')
    print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/21_match_bootstrap_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print('Observed shares (%):', evidence['observed_shares_pct'])
    print('Observed difference (percentage points):', evidence['observed_difference_percentage_points'])
    print('Illustrative percentile interval (percentage points):', evidence['illustrative_interval_percentage_points'])
    print('Valid / zero-denominator resamples:', evidence['valid_resamples'], evidence['zero_denominator_resamples'])
    print('First illustrative draw (match IDs):', evidence['example_match_ids'])
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
