# Soccermatics Lesson 2 adaptation: a small, educational distance-only xG model.
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson2/plot_xGModelFit.html
# Uses our seven cached games, both teams, excluding penalties and shootouts.
from pathlib import Path
from collections import Counter
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parent
base = json.loads((ROOT / 'data/11_tournament_passes_evidence.json').read_text())
train_ids, test_ids = base['match_ids'][:5], base['match_ids'][5:]
assert set(train_ids).isdisjoint(test_ids)
rows, exclusions = [], Counter()
for match_id in base['match_ids']:
    events = json.loads((ROOT / f'data/cache_2019_events/{match_id}.json').read_text())
    for e in events:
        if e['type']['name'] != 'Shot':
            continue
        if e['period'] >= 5 or e['shot'].get('type', {}).get('name') == 'Penalty':
            exclusions['penalties_or_shootout'] += 1
            continue
        if 'location' not in e:
            exclusions['missing_location'] += 1
            continue
        x, y = e['location'][:2]
        assert 0 <= x <= 120 and 0 <= y <= 80
        # Distance to goal centre (120,40), in standardised StatsBomb coordinate units.
        # These are NOT measured metres on each match's actual pitch.
        distance = float(np.hypot(120 - x, 40 - y))
        rows.append({'match_id': match_id, 'id': e['id'], 'team': e['team']['name'],
                     'player': e['player']['name'], 'x': x, 'y': y, 'distance': distance,
                     'goal': int(e['shot']['outcome']['name'] == 'Goal'),
                     'body_part': e['shot']['body_part']['name'],
                     'split': 'train' if match_id in train_ids else 'test'})
assert len({(r['match_id'], r['id']) for r in rows}) == len(rows)
train = [r for r in rows if r['split'] == 'train']
test = [r for r in rows if r['split'] == 'test']
train_d = np.array([r['distance'] for r in train])
train_y = np.array([r['goal'] for r in train])
test_d = np.array([r['distance'] for r in test])
test_y = np.array([r['goal'] for r in test])
assert 0 < train_y.sum() < len(train_y) and 0 < test_y.sum() < len(test_y)

# Fit the distance scaling from TRAINING data only, then apply it unchanged to test.
mean_distance, scale_distance = float(train_d.mean()), float(train_d.std())
assert scale_distance > 0
train_x = np.column_stack([np.ones(len(train)), (train_d - mean_distance) / scale_distance])
test_x = np.column_stack([np.ones(len(test)), (test_d - mean_distance) / scale_distance])

# Logistic regression: probability = sigmoid(intercept + slope * scaled distance).
# Minimise training log loss. No provider xG is used as a feature or target.
def objective(beta):
    z = train_x @ beta
    loss = np.mean(np.logaddexp(0, z) - train_y * z)
    gradient = train_x.T @ (expit(z) - train_y) / len(train_y)
    return loss, gradient

fit = minimize(objective, np.zeros(2), jac=True, method='BFGS', options={'gtol': 1e-8})
assert fit.success, fit.message
test_predictions = expit(test_x @ fit.x)
assert np.isfinite(test_predictions).all() and ((test_predictions > 0) & (test_predictions < 1)).all()

# A baseline predicts the TRAINING goal rate for every unseen test shot.
baseline_probability = float(train_y.mean())
baseline_predictions = np.full(len(test), baseline_probability)
def evaluate(y, probability):
    p = np.clip(probability, 1e-12, 1 - 1e-12)
    return {'brier_score': float(np.mean((p - y) ** 2)),
            'log_loss': float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
            'predicted_goal_total': float(p.sum())}

model_metrics = evaluate(test_y, test_predictions)
baseline_metrics = evaluate(test_y, baseline_predictions)
for row, probability in zip(test, test_predictions):
    row['predicted_xg'] = float(probability)
for row in train:
    row['predicted_xg'] = float(expit(fit.x[0] + fit.x[1] * (row['distance'] - mean_distance) / scale_distance))
print(f'Train: {len(train)} shots, {int(train_y.sum())} goals, five complete matches')
print(f'Test: {len(test)} shots, {int(test_y.sum())} goals, two unseen complete matches')
print('Exclusions:', dict(exclusions))
print(f'Constant training-rate baseline: {baseline_probability:.2%}')
print('Distance model test scores:',model_metrics)
print('Constant baseline test scores:',baseline_metrics)

distances = np.linspace(train_d.min(), train_d.max(), 200)
curve = expit(fit.x[0] + fit.x[1] * (distances - mean_distance) / scale_distance)
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
fig.subplots_adjust(left=0.08, right=0.96, top=0.77, bottom=0.23, wspace=0.25)
axes[0].plot(distances, curve, color='#24658a', lw=2, label='Fitted distance-only model')
axes[0].axhline(baseline_probability, color='#687078', ls='--', label='Constant training goal rate')
bin_edges = np.arange(0, np.ceil(train_d.max() / 10) * 10 + 1, 10)
for low, high in zip(bin_edges[:-1], bin_edges[1:]):
    mask = (train_d >= low) & (train_d < high)
    n = int(mask.sum())
    if n:
        goals = int(train_y[mask].sum())
        axes[0].scatter((low + high) / 2, goals / n, color='#222222', s=40, zorder=3)
        axes[0].annotate(f'{goals}/{n}', ((low + high) / 2, goals / n),
                         xytext=(0, 8), textcoords='offset points', ha='center', fontsize=9)
axes[0].set(xlabel='Distance to goal centre (StatsBomb coordinate units)',
            ylabel='Estimated goal probability', ylim=(-0.02, 1.02), xlim=(0, train_d.max()))
axes[0].set_title('Learn a probability curve from training shots', fontsize=12)
axes[0].legend(frameon=False, fontsize=9, loc='upper right')
axes[1].bar(['Constant baseline', 'Distance model'],
             [baseline_metrics['brier_score'], model_metrics['brier_score']], color=['#687078', '#24658a'], width=0.55)
for i, value in enumerate([baseline_metrics['brier_score'], model_metrics['brier_score']]):
    axes[1].text(i, value + 0.003, f'{value:.4f}', ha='center', fontsize=11)
axes[1].set_ylabel('Test Brier score: mean squared probability error')
axes[1].set_ylim(0, max(baseline_metrics['brier_score'], model_metrics['brier_score']) * 1.25)
axes[1].set_title('Evaluate on unseen matches — lower is better', fontsize=12)
for ax in axes:
    ax.grid(axis='y', color='#e4e7ea')
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
fig.suptitle('First educational xG model: distance, training and testing', fontsize=20, weight='bold', y=0.96)
fig.text(0.5, 0.85,
         f'Both teams in seven England 2019 World Cup fixtures · Non-penalty shots\n'
         f'Train: first five matches ({len(train)} shots) · Test: USA and Sweden fixtures ({len(test)} shots)',
         ha='center', fontsize=11)
fig.text(0.5, 0.055,
         'Black points: observed training-bin goal rates (labels: goals/shots) · Small, selected sample; no general performance claim\n'
         'No provider xG, shot outcome, angle, body part or defensive context used as input · Source: StatsBomb Open Data; Soccermatics Lesson 2',
         ha='center', fontsize=9)
figure = ROOT / 'figures/21_first_xg_distance_model.png'
fig.savefig(figure, dpi=180, bbox_inches='tight')
evidence = {'model': 'Educational distance-only logistic regression',
            'training_match_ids': train_ids, 'test_match_ids': test_ids,
            'feature': 'Euclidean distance to goal centre in StatsBomb coordinate units',
            'training_mean_distance': mean_distance, 'training_scale_distance': scale_distance,
            'training_distance_range': [float(train_d.min()), float(train_d.max())],
            'test_distance_range': [float(test_d.min()), float(test_d.max())],
            'intercept_scaled': float(fit.x[0]), 'distance_coefficient_scaled': float(fit.x[1]),
            'optimisation_success': bool(fit.success), 'training_shots': len(train),
            'training_goals': int(train_y.sum()), 'test_shots': len(test), 'test_goals': int(test_y.sum()),
            'baseline_training_goal_rate': baseline_probability, 'model_test_metrics': model_metrics,
            'baseline_test_metrics': baseline_metrics, 'exclusions': dict(exclusions), 'shots': rows}
(ROOT / 'data/18_first_xg_model_evidence.json').write_text(json.dumps(evidence, indent=2))
print('Saved:',figure)
plt.show()
