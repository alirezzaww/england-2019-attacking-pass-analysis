"""Lesson 26: inspect calibration of the selected candidate's out-of-fold probabilities.

Uses the 114 training-only held-out predictions saved in lesson 25. These predictions
were used for candidate selection, so this is exploratory development inspection,
not a fresh evaluation or a calibration claim for the final refitted model.
No recalibrator is fitted. Provider xG in the passing analysis remains unchanged.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDGES = (0, 0.05, 0.10, 0.20, 1)


def probability_bin(probability):
    """Left-closed, right-open bins, except the last bin includes probability 1."""
    if not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError('Probability must be finite and between zero and one')
    for j, (low, high) in enumerate(zip(EDGES[:-1], EDGES[1:])):
        if low <= probability < high or j == len(EDGES) - 2 and probability == high:
            return j
    raise ValueError('Probability did not belong to a bin')


def calibration_bins(rows):
    """Compare mean prediction with goal frequency; missing groups stay undefined."""
    identities = {(r['match_id'], r['id']) for r in rows}
    if len(identities) != len(rows):
        raise ValueError('Duplicate shot identity in calibration sample')
    groups = [[] for _ in EDGES[:-1]]
    for row in rows:
        if row['goal'] not in [0, 1]:
            raise ValueError('Goal target must be binary')
        groups[probability_bin(row['predicted_probability'])].append(row)
    output = []
    for j, group in enumerate(groups):
        n, goals = len(group), sum(r['goal'] for r in group)
        expected = sum(r['predicted_probability'] for r in group)
        output.append({'bin_index': j, 'lower_inclusive': EDGES[j], 'upper': EDGES[j + 1],
                       'upper_inclusive': j == len(groups) - 1,
                       'shots': n, 'goals': goals, 'predicted_goal_sum': expected,
                       'mean_predicted_probability': expected / n if n else None,
                       'observed_goal_fraction': goals / n if n else None,
                       'shot_ids': [{'match_id': r['match_id'], 'id': r['id']} for r in group]})
    return output


def build_evidence():
    source = json.loads((ROOT / 'data/25_shot_angle_evidence.json').read_text())
    name = source['selected_candidate']
    shot_lookup = {(r['match_id'], r['id']): r for r in source['shots']}
    rows = []
    for fold in source['candidates'][name]['validation_folds']:
        match_id = fold['validation_match_id']
        assert match_id in source['training_match_ids'] and match_id not in source['reused_test_match_ids']
        assert len(fold['validation_shot_ids']) == len(fold['predictions']), 'Prediction and identity lengths differ'
        for identity, probability in zip(fold['validation_shot_ids'], fold['predictions']):
            shot = shot_lookup[(match_id, identity)]
            assert shot['split'] == 'train'
            rows.append({'match_id': match_id, 'id': identity, 'goal': shot['goal'],
                         'predicted_probability': probability})
    bins = calibration_bins(rows)
    n = len(rows)
    assert n == 114 and sum(b['shots'] for b in bins) == n
    return {'source': '25_shot_angle_evidence.json', 'selected_candidate': name,
            'prediction_source': 'Training-only leave-one-match-out validation folds; reused after candidate selection',
            'match_ids': source['training_match_ids'], 'bin_edges': list(EDGES),
            'summary': {'shots': n, 'goals': sum(r['goal'] for r in rows),
                        'predicted_goal_sum': sum(r['predicted_probability'] for r in rows),
                        'mean_predicted_probability': sum(r['predicted_probability'] for r in rows) / n,
                        'observed_goal_fraction': sum(r['goal'] for r in rows) / n},
            'bins': bins, 'predictions': rows,
            'interpretation_limit': '114 selected shots, 11 goals and five fixtures; binned post-selection diagnostic of fold-specific fits, no fresh evaluation, confidence interval or recalibration'}


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.25, wspace=0.25)
    observed = [b for b in evidence['bins'] if b['shots']]
    axes[0].plot([0, 35], [0, 35], color='#687e8c', linestyle='--', label='Equal predicted and observed rates')
    axes[0].scatter([b['mean_predicted_probability'] * 100 for b in observed],
                    [b['observed_goal_fraction'] * 100 for b in observed], color='#24658a', s=70, zorder=3)
    for row in observed:
        axes[0].annotate(f"{row['goals']}/{row['shots']}",
                         (row['mean_predicted_probability'] * 100, row['observed_goal_fraction'] * 100),
                         xytext=(6, 8), textcoords='offset points', fontsize=10)
    axes[0].set(xlim=(0, 35), ylim=(-1, 35), xlabel='Mean predicted goal probability in group (%)',
                ylabel='Observed goals / shots in group (%)')
    axes[0].set_title('Do grouped probabilities match goal frequency?')
    axes[0].legend(frameon=False, fontsize=8, loc='upper left')
    labels = ['0–<5%', '5–<10%', '10–<20%', '20–100%']
    axes[1].bar(labels, [b['shots'] for b in evidence['bins']], color='#24658a', width=0.6)
    for j, row in enumerate(evidence['bins']):
        axes[1].text(j, row['shots'] + 0.8, f"{row['shots']} shots\n{row['goals']} goals", ha='center', fontsize=10)
    axes[1].set_ylim(0, max(b['shots'] for b in evidence['bins']) * 1.25)
    axes[1].set_xlabel('Predicted goal probability group (fixed boundaries)')
    axes[1].set_ylabel('Number of held-out shot predictions')
    axes[1].set_title('How much data supports each point?')
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea'); ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('Probability calibration: inspect the selected distance candidate', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, '114 out-of-fold non-penalty shots, 11 goals · Both teams in the first five England 2019 World Cup fixtures\nEach shot’s fitting model excluded its fixture; predictions are reused from candidate selection', ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'Left labels are goals/shots; points are bin averages, not individual shots · Small groups and linked match events limit interpretation.\nExploratory diagnostic of five fold-specific fits; no fresh calibration validation, confidence intervals or recalibration.\nSource: StatsBomb Open Data · Probability-calibration method: scikit-learn documentation', ha='center', fontsize=9)
    path = ROOT / 'figures/29_probability_calibration.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/26_calibration_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print('Selected candidate:', evidence['selected_candidate'])
    print('Summary:', evidence['summary'])
    for row in evidence['bins']:
        predicted = f"{row['mean_predicted_probability']:.2%}" if row['shots'] else 'undefined'
        observed = f"{row['observed_goal_fraction']:.2%}" if row['shots'] else 'undefined'
        print(f"{row['lower_inclusive']:.0%} to {row['upper']:.0%}: {row['shots']} shots, {row['goals']} goals; "
              f"mean predicted {predicted}, observed {observed}")
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
