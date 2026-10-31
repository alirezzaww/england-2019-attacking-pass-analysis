"""Lesson 28: inspect the training-distance pattern and flag extrapolation.

This is a post-evaluation diagnostic using the frozen lesson-27 model. No fitting,
new validation, model changes or retrospective exclusions are performed.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COVERAGE = ('Closer than training range', 'Inside training range', 'Farther than training range')


def distance_band(distance):
    if not isinstance(distance, (int, float)) or not math.isfinite(distance) or distance < 0:
        raise ValueError('Distance must be finite and nonnegative')
    return 0 if distance < 10 else 1 if distance < 20 else 2 if distance < 30 else 3


def range_category(distance, lower, upper):
    distance_band(distance)
    if not all(math.isfinite(v) for v in [lower, upper]) or not 0 <= lower <= upper:
        raise ValueError('Invalid training distance range')
    return COVERAGE[0] if distance < lower else COVERAGE[2] if distance > upper else COVERAGE[1]


def summarize_group(rows):
    n = len(rows)
    return {'shots': n, 'goals': sum(r['goal'] for r in rows),
            'observed_goal_fraction': sum(r['goal'] for r in rows) / n if n else None,
            'mean_distance_template_m': sum(r['distance_template_m'] for r in rows) / n if n else None,
            'min_distance_template_m': min((r['distance_template_m'] for r in rows), default=None),
            'max_distance_template_m': max((r['distance_template_m'] for r in rows), default=None),
            'shot_ids': [{'match_id': r['match_id'], 'id': r['id']} for r in rows]}


def build_evidence():
    protocol_path = ROOT / 'data/27_evaluation_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    evaluation = json.loads((ROOT / 'data/27_frozen_evaluation_evidence.json').read_text())
    source = json.loads((ROOT / 'data/25_shot_angle_evidence.json').read_text())
    assert evaluation['protocol_sha256'] == hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    code = ROOT / protocol['source_model_code']
    assert hashlib.sha256(code.read_bytes()).hexdigest() == protocol['source_model_code_sha256']
    spec = importlib.util.spec_from_file_location('support_frozen_model', code)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    assert protocol['frozen_fit']['features'] == ['distance_template_m']
    train = [r for r in source['shots'] if r['split'] == 'train']
    assert len(train) == protocol['training_shots'] == 114
    lower, upper = min(r['distance_template_m'] for r in train), max(r['distance_template_m'] for r in train)
    bands = []
    for j, start in enumerate([0, 10, 20, 30]):
        rows = [r for r in train if distance_band(r['distance_template_m']) == j]
        bands.append({'lower_inclusive_m': start, 'upper_exclusive_m': [10, 20, 30, None][j], **summarize_group(rows)})
    coverage = [{'category': category, **summarize_group([r for r in evaluation['shots']
                if range_category(r['distance_template_m'], lower, upper) == category])} for category in COVERAGE]
    examples = [{'distance_template_m': d, 'frozen_probability': helper.predict(protocol['frozen_fit'], {'distance_template_m': d})}
                for d in [10, 20, 30]]
    return {'sources': ['25_shot_angle_evidence.json', '27_evaluation_protocol.json', '27_frozen_evaluation_evidence.json'],
            'protocol_sha256': evaluation['protocol_sha256'], 'training_distance_range_template_m': [lower, upper],
            'distance_unit': 'Metres on the assumed 105x68 reference pitch, not measured venue dimensions',
            'training_bands': bands, 'evaluation_coverage': coverage, 'example_predictions': examples,
            'frozen_baseline_probability': helper.predict(protocol['frozen_baseline_fit'], {}),
            'training_shots': len(train), 'evaluation_shots': len(evaluation['shots']),
            'interpretation_limit': 'In-sample training pattern and post-evaluation coverage audit only; range overlap is not full data support or reliability; zero sample goals is not zero scoring probability'}


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    protocol = json.loads((ROOT / 'data/27_evaluation_protocol.json').read_text())
    fit = protocol['frozen_fit']
    def probability(distance):
        z = fit['coefficients'][0] + fit['coefficients'][1] * (distance - fit['means'][0]) / fit['scales'][0]
        return 100 / (1 + math.exp(-z))
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.76, bottom=0.25, wspace=0.28)
    low, high = evidence['training_distance_range_template_m']
    for start, end, style, label in [(0, low, '--', 'Model curve outside training range'),
                                    (low, high, '-', 'Model curve inside training range'),
                                    (high, 55, '--', None)]:
        distances = [start + (end - start) * j / 100 for j in range(101)]
        axes[0].plot(distances, [probability(d) for d in distances], color='#24658a', linestyle=style, label=label)
    for j, band in enumerate(evidence['training_bands']):
        if not band['shots']:
            continue
        x, y = band['mean_distance_template_m'], band['observed_goal_fraction'] * 100
        axes[0].scatter(x, y, color='#b77516', s=55, zorder=3, label='Observed training-group goal rate' if j == 0 else None)
        axes[0].annotate(f"{band['goals']}/{band['shots']}", (x, y), xytext=(5, 9), textcoords='offset points', fontsize=10)
    axes[0].axhline(evidence['frozen_baseline_probability'] * 100, color='#687e8c', linestyle=':', label='Constant baseline: 9.65%')
    axes[0].set(xlim=(0, 55), ylim=(-2, 52), xlabel='Distance to goal centre on reference pitch (m)', ylabel='Goal probability / observed goal rate (%)')
    axes[0].set_title('See the training pattern and the fitted formula')
    axes[0].legend(frameon=False, fontsize=8, loc='upper right')
    coverage = evidence['evaluation_coverage']
    axes[1].bar(range(3), [r['shots'] for r in coverage], color=['#b77516', '#24658a', '#b77516'], width=0.55)
    for j, row in enumerate(coverage):
        axes[1].text(j, row['shots'] + 18, f"{row['shots']} shots\n{row['goals']} goals", ha='center', fontsize=10)
    axes[1].set_xticks(range(3), ['Closer than\ntraining minimum', 'Inside observed\ntraining range', 'Farther than\ntraining maximum'])
    axes[1].set_ylim(0, max(r['shots'] for r in coverage) * 1.22)
    axes[1].set_ylabel('Previously evaluated shots (count)')
    axes[1].set_title(f'Evaluation distance coverage: training {low:.2f}–{high:.2f} m')
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea'); ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('Understand what the model learned—and where its data stops', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, 'Left: 114 training shots, in-sample description only · Right: the same 1,131 already inspected evaluation shots\nModel, baseline and previous evaluation inclusion rules stay unchanged', ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'Training dots show grouped goals/shots; the model was fitted to individual shots, not to these dots.\nDashed blue = distance extrapolation; being inside the range does not establish reliable xG or full contextual support.\nReference-pitch metres are assumed, not measured stadium geometry · Source: StatsBomb Open Data', ha='center', fontsize=9)
    path = ROOT / 'figures/31_training_distance_support.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/28_distance_support_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print('Training range:', evidence['training_distance_range_template_m'])
    for row in evidence['training_bands']:
        print('Training band:', row['lower_inclusive_m'], row['upper_exclusive_m'], row['goals'], '/', row['shots'])
    for row in evidence['evaluation_coverage']:
        print(row['category'], row['shots'], 'shots;', row['goals'], 'goals')
    print('Actual frozen-model examples:', evidence['example_predictions'])
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
