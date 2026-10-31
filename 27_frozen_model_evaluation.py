"""Lesson 27: evaluate the frozen lesson-25 model on 45 previously unused fixtures.

Read the committed protocol BEFORE downloading new shot events. No fitting, feature
selection or metric tuning occurs here. Raw inputs are cached outside Git; saved
predictions, input hashes and paired whole-match resampling remain auditable.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / 'data/27_evaluation_protocol.json'
CACHE = ROOT / 'data/cache_2019_events'


def load_helper(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cache_fixture(match_id):
    import requests
    path = CACHE / f'{match_id}.json'
    if not path.is_file():
        response = requests.get(f'https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json', timeout=60)
        response.raise_for_status()
        events = response.json()
        if not isinstance(events, list):
            raise ValueError('Expected an event list')
        path.write_bytes(response.content)
    return {'match_id': match_id, 'relative_path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_url': f'https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json'}


def per_shot_losses(goal, probability):
    p = min(max(probability, 1e-12), 1 - 1e-12)
    return {'log_loss': -(goal * math.log(p) + (1 - goal) * math.log(1 - p)),
            'brier_score': (probability - goal) ** 2}


def aggregate_difference(match_summaries, indices, metric):
    """Pool shot losses after paired whole-match selection; negative favours model."""
    n = sum(match_summaries[i]['shots'] for i in indices)
    if not n:
        return None
    return sum(match_summaries[i]['model_loss_sums'][metric] - match_summaries[i]['baseline_loss_sums'][metric]
               for i in indices) / n


def resample_differences(match_summaries, configuration):
    rng = random.Random(configuration['seed'])
    differences = {'log_loss': [], 'brier_score': []}
    invalid = 0
    for _ in range(configuration['n_resamples']):
        indices = [rng.randrange(len(match_summaries)) for _ in match_summaries]
        values = {metric: aggregate_difference(match_summaries, indices, metric) for metric in differences}
        if values['log_loss'] is None:
            invalid += 1
        else:
            for metric in differences:
                differences[metric].append(values[metric])
    return differences, invalid


def linear_quantile(values, q):
    if not values or not 0 <= q <= 1:
        raise ValueError('Expected nonempty values and a quantile from zero to one')
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def build_evidence():
    protocol = json.loads(PROTOCOL.read_text())
    code = ROOT / protocol['source_model_code']
    if hashlib.sha256(code.read_bytes()).hexdigest() != protocol['source_model_code_sha256']:
        raise ValueError('Frozen model code changed; do not silently change the evaluation protocol')
    model = load_helper(protocol['source_model_code'], 'frozen_geometry_model')
    calibration = load_helper('26_probability_calibration.py', 'evaluation_calibration')
    assert list(calibration.EDGES) == protocol['calibration_bin_edges']
    matches = protocol['evaluation_match_ids']
    assert len(matches) == len(set(matches)) == 45
    assert set(matches).isdisjoint(protocol['excluded_previously_used_match_ids'])
    CACHE.mkdir(parents=True, exist_ok=True)
    raw_inputs = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(cache_fixture, match_id): match_id for match_id in matches}
        for number, future in enumerate(as_completed(pending), 1):
            record = future.result(); raw_inputs[record['match_id']] = record
            if number % 5 == 0 or number == len(matches):
                print(f'Cached {number}/{len(matches)} evaluation fixtures', flush=True)
    rows, excluded = [], []
    fixture_metadata = {m['match_id']: m for m in protocol['fixture_metadata']}
    for match_id in matches:
        events = json.loads((CACHE / f'{match_id}.json').read_text())
        expected_teams = {fixture_metadata[match_id]['home_team'], fixture_metadata[match_id]['away_team']}
        assert {e['team']['name'] for e in events} == expected_teams, 'Event file does not match fixture teams'
        for event in events:
            if event['type']['name'] != 'Shot':
                continue
            reason = None
            if event['period'] >= 5:
                reason = 'shootout'
            elif event['shot'].get('type', {}).get('name') == 'Penalty':
                reason = 'penalty'
            elif 'location' not in event or len(event['location']) < 2:
                reason = 'missing_location'
            else:
                x, y = event['location'][:2]
                try:
                    distance, angle = model.shot_geometry(x, y)
                except ValueError:
                    reason = 'invalid_geometry'
            if reason:
                excluded.append({'match_id': match_id, 'id': event['id'], 'reason': reason})
                continue
            row = {'match_id': match_id, 'id': event['id'], 'x': x, 'y': y,
                   'goal': int(event['shot']['outcome']['name'] == 'Goal'),
                   'distance_template_m': distance, 'angle_radians': angle}
            row['model_probability'] = model.predict(protocol['frozen_fit'], row)
            row['baseline_probability'] = model.predict(protocol['frozen_baseline_fit'], row)
            rows.append(row)
    assert len({(r['match_id'], r['id']) for r in rows}) == len(rows)
    scores = {name: model.score_predictions([r['goal'] for r in rows], [r[f'{name}_probability'] for r in rows])
              for name in ['model', 'baseline']}
    summaries = []
    for match_id in matches:
        group = [r for r in rows if r['match_id'] == match_id]
        saved = {'match_id': match_id, 'shots': len(group), 'goals': sum(r['goal'] for r in group)}
        for name in ['model', 'baseline']:
            losses = [per_shot_losses(r['goal'], r[f'{name}_probability']) for r in group]
            saved[f'{name}_loss_sums'] = {metric: sum(v[metric] for v in losses) for metric in ['log_loss', 'brier_score']}
        summaries.append(saved)
    differences, invalid = resample_differences(summaries, protocol['bootstrap'])
    intervals = {metric: [linear_quantile(values, q) for q in protocol['bootstrap']['percentiles']]
                 for metric, values in differences.items()}
    calibration_rows = [{'match_id': r['match_id'], 'id': r['id'], 'goal': r['goal'],
                         'predicted_probability': r['model_probability']} for r in rows]
    return {'protocol_path': 'data/27_evaluation_protocol.json',
            'protocol_sha256': hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
            'evaluation_match_ids': matches, 'training_shots_unchanged': protocol['training_shots'],
            'evaluation_shots': len(rows), 'evaluation_goals': sum(r['goal'] for r in rows),
            'model_metrics': scores['model'], 'baseline_metrics': scores['baseline'],
            'model_minus_baseline': {m: scores['model'][m] - scores['baseline'][m] for m in ['log_loss', 'brier_score']},
            'paired_match_bootstrap_intervals': intervals,
            'bootstrap_valid_draws': len(differences['log_loss']), 'bootstrap_invalid_draws': invalid,
            'calibration_bins': calibration.calibration_bins(calibration_rows),
            'match_summaries': summaries, 'shots': rows, 'excluded_shots': excluded,
            'exclusion_counts': dict(Counter(r['reason'] for r in excluded)),
            'raw_inputs': [raw_inputs[m] for m in matches],
            'scope_limit': protocol['scope_limit'],
            'interpretation_limit': 'Fixed-model check on new fixture shot events; same tournament, shared teams, non-England sample. Bootstrap assumes exchangeable match sampling. No practical readiness or new-season reliability claim.'}


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.25, wspace=0.27)
    values = [evidence['baseline_metrics']['log_loss'], evidence['model_metrics']['log_loss']]
    axes[0].bar(['Frozen constant baseline', 'Frozen distance model'], values, color=['#687e8c', '#24658a'], width=0.55)
    for j, value in enumerate(values):
        axes[0].text(j, value + 0.006, f'{value:.4f}', ha='center')
    axes[0].set_ylim(0, max(values) * 1.25)
    axes[0].set_ylabel('Evaluation log loss (lower is better)')
    axes[0].set_title('Fixed model versus fixed simple baseline')
    axes[1].plot([0, 45], [0, 45], linestyle='--', color='#687e8c', label='Equal predicted and observed rates')
    for row in evidence['calibration_bins']:
        if row['shots']:
            x, y = row['mean_predicted_probability'] * 100, row['observed_goal_fraction'] * 100
            axes[1].scatter(x, y, color='#24658a', s=65)
            axes[1].annotate(f"{row['goals']}/{row['shots']}", (x, y), xytext=(6, 8), textcoords='offset points', fontsize=9)
    axes[1].set(xlim=(0, 45), ylim=(-1, 45), xlabel='Mean predicted probability in group (%)', ylabel='Observed goals / shots in group (%)')
    axes[1].set_title('New-fixture calibration diagnostic')
    axes[1].legend(frameon=False, fontsize=8, loc='upper left')
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea'); ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('Keep the model fixed; check previously unused fixtures', fontsize=20, weight='bold', y=0.96)
    fig.text(0.5, 0.84, f"{len(evidence['evaluation_match_ids'])} other 2019 Women’s World Cup fixtures · {evidence['evaluation_shots']} non-penalty shots, {evidence['evaluation_goals']} goals\nModel still trained on 114 shots; all seven development fixtures excluded · Protocol committed before new event downloads", ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'Both teams’ shots; penalties, shootouts and unscorable geometry excluded by frozen rules. Right labels are goals/shots.\nSame tournament, non-England fixtures and shared teams limit generalisation; this is not a practical-readiness certification.\nSource: StatsBomb Open Data · Frozen model from project lesson 25', ha='center', fontsize=9)
    path = ROOT / 'figures/30_frozen_model_evaluation.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/27_frozen_evaluation_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    for key in ['evaluation_shots', 'evaluation_goals', 'exclusion_counts', 'model_metrics', 'baseline_metrics', 'model_minus_baseline', 'paired_match_bootstrap_intervals']:
        print(key, evidence[key], flush=True)
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
