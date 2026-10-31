"""Lesson 25: compare distance-only and distance-plus-angle xG candidates.

Geometry follows Soccermatics Lesson 2 on a normalised 105 x 68 reference pitch.
Candidate selection uses leave-one-match-out validation inside the FIRST FIVE games.
The last two games were inspected in lesson 18 and are a reused exploratory check.
This small educational comparison does not change provider xG in the pass study.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANDIDATES = {'constant': [], 'distance': ['distance_template_m'],
              'distance_angle': ['distance_template_m', 'angle_radians']}


def shot_geometry(x, y):
    """Map StatsBomb coordinates to a 105x68 reference; return distance and opening angle."""
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in [x, y]) or not (0 <= x <= 120 and 0 <= y <= 80):
        raise ValueError('Shot coordinates must be finite and inside the StatsBomb pitch')
    dx, lateral = (120 - x) * 105 / 120, (y - 40) * 68 / 80
    distance = math.hypot(dx, lateral)
    # atan2 retains the correct quadrant close to goal. Exact goalpost locations are undefined.
    denominator = dx * dx + lateral * lateral - (7.32 / 2) ** 2
    if dx == 0 and abs(denominator) < 1e-12:
        raise ValueError('Opening angle is undefined at an exact goalpost')
    return distance, math.atan2(7.32 * dx, denominator)


def predict(fit, row):
    z = fit['coefficients'][0]
    for j, name in enumerate(fit['features']):
        z += fit['coefficients'][j + 1] * (row[name] - fit['means'][j]) / fit['scales'][j]
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    exponent = math.exp(z)
    return exponent / (1 + exponent)


def score_predictions(labels, predictions):
    if not labels or len(labels) != len(predictions):
        raise ValueError('Provide matching, nonempty labels and probabilities')
    if any(y not in [0, 1] for y in labels) or any(not math.isfinite(p) or not 0 <= p <= 1 for p in predictions):
        raise ValueError('Targets must be binary and probabilities between zero and one')
    clipped = [min(max(p, 1e-12), 1 - 1e-12) for p in predictions]
    return {'brier_score': sum((p - y) ** 2 for y, p in zip(labels, predictions)) / len(labels),
            'log_loss': -sum(y * math.log(p) + (1 - y) * math.log(1 - p) for y, p in zip(labels, clipped)) / len(labels),
            'predicted_goal_total': sum(predictions)}


def leave_one_match_out(rows, match_ids):
    """Return fixture-disjoint fit/validation subsets; callers supply training games only."""
    if set(r['match_id'] for r in rows) != set(match_ids) or len(set(match_ids)) != len(match_ids):
        raise ValueError('Training rows and unique fixture IDs must agree')
    return [(m, [r for r in rows if r['match_id'] != m], [r for r in rows if r['match_id'] == m]) for m in match_ids]


def fit_logistic(rows, features):
    import numpy as np
    from scipy.optimize import minimize
    from scipy.special import expit
    y = np.array([r['goal'] for r in rows], dtype=float)
    if not 0 < y.mean() < 1:
        raise ValueError('The fitting subset needs goals and non-goals')
    if not features:
        probability = float(y.mean())
        return {'features': [], 'means': [], 'scales': [],
                'coefficients': [math.log(probability / (1 - probability))], 'converged': True}
    raw = np.array([[r[f] for f in features] for r in rows], dtype=float)
    means, scales = raw.mean(axis=0), raw.std(axis=0)
    if not (scales > 0).all():
        raise ValueError('Every feature needs variation in the fitting subset')
    design = np.column_stack([np.ones(len(rows)), (raw - means) / scales])
    def objective(beta):
        z = design @ beta
        return float(np.mean(np.logaddexp(0, z) - y * z)), design.T @ (expit(z) - y) / len(y)
    result = minimize(objective, np.zeros(len(features) + 1), jac=True, method='BFGS', options={'gtol': 1e-7})
    if not result.success:
        raise RuntimeError(f'Logistic optimiser did not converge: {result.message}')
    return {'features': list(features), 'means': means.tolist(), 'scales': scales.tolist(),
            'coefficients': result.x.tolist(), 'converged': bool(result.success)}


def build_evidence():
    source = json.loads((ROOT / 'data/18_first_xg_model_evidence.json').read_text())
    rows = []
    for original in source['shots']:
        distance, angle = shot_geometry(original['x'], original['y'])
        rows.append({**{k: original[k] for k in ['match_id', 'id', 'x', 'y', 'goal', 'split', 'body_part']},
                     'distance_template_m': distance, 'angle_radians': angle})
    train, test = [r for r in rows if r['split'] == 'train'], [r for r in rows if r['split'] == 'test']
    folds = leave_one_match_out(train, source['training_match_ids'])
    candidates = {}
    for name, features in CANDIDATES.items():
        saved_folds, labels, probabilities = [], [], []
        for validation_id, fitting_rows, validation_rows in folds:
            fit = fit_logistic(fitting_rows, features)
            predicted = [predict(fit, r) for r in validation_rows]
            saved_folds.append({'validation_match_id': validation_id,
                                'fitting_match_ids': [m for m in source['training_match_ids'] if m != validation_id],
                                'fit': fit, 'validation_shot_ids': [r['id'] for r in validation_rows],
                                'predictions': predicted})
            labels.extend(r['goal'] for r in validation_rows); probabilities.extend(predicted)
        candidates[name] = {'features': features, 'validation_folds': saved_folds,
                            'validation_metrics': score_predictions(labels, probabilities)}
    # Fix selection from training-only log loss BEFORE inspecting the reused last-two-game scores.
    selected = min(candidates, key=lambda name: candidates[name]['validation_metrics']['log_loss'])
    for name, features in CANDIDATES.items():
        fit = fit_logistic(train, features)
        predictions = [predict(fit, r) for r in test]
        candidates[name].update({'fit_all_training': fit, 'reused_test_shot_ids': [r['id'] for r in test],
                                'reused_test_predictions': predictions,
                                'reused_test_metrics': score_predictions([r['goal'] for r in test], predictions)})
    return {'source': '18_first_xg_model_evidence.json',
            'geometry': 'StatsBomb x,y mapped to normalised 105x68 reference; goal width 7.32, not measured venue dimensions',
            'training_match_ids': source['training_match_ids'], 'reused_test_match_ids': source['test_match_ids'],
            'primary_selection_metric': 'pooled training-only leave-one-match-out log loss',
            'selected_candidate': selected, 'shots': rows, 'candidates': candidates,
            'interpretation_limit': '150 selected shots; only five training fixtures; final two fixtures previously inspected; no fresh external evaluation or production xG claim'}


def plot_evidence(evidence):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.77, bottom=0.23, wspace=0.28)
    goal_x, posts = 105, [34 - 3.66, 34 + 3.66]
    axes[0].plot([105, 105], [12, 56], color='#687e8c', linewidth=1)
    axes[0].plot([105, 105], posts, color='#172d3b', linewidth=4, label='Goal mouth')
    for (x, y), color, label in [((90, 34), '#24658a', 'Central'), ((96, 46), '#b77516', 'Wider')]:
        _, angle = shot_geometry(x * 120 / 105, y * 80 / 68)
        for post in posts:
            axes[0].plot([x, goal_x], [y, post], color=color, alpha=0.8)
        axes[0].scatter(x, y, color=color, s=60, zorder=3)
        axes[0].annotate(f'{label}: 15 m\n{math.degrees(angle):.1f}° opening', (x, y),
                         xytext=(-5, 12), textcoords='offset points', ha='right', color=color, fontsize=10)
    axes[0].set(xlim=(82, 108), ylim=(18, 53), xlabel='Reference-pitch length (m)', ylabel='Reference-pitch width (m)')
    axes[0].set_aspect('equal', adjustable='box')
    axes[0].set_title('Same distance, different goal opening')
    names = list(CANDIDATES)
    errors = [evidence['candidates'][n]['validation_metrics']['log_loss'] for n in names]
    axes[1].bar(['Constant', 'Distance', 'Distance + angle'], errors, color=['#687e8c', '#24658a', '#b77516'], width=0.55)
    for i, value in enumerate(errors):
        axes[1].text(i, value + 0.008, f'{value:.4f}', ha='center')
    axes[1].set_ylim(0, max(errors) * 1.25)
    axes[1].set_ylabel('Pooled held-out-match log loss (lower is better)')
    axes[1].set_title('Training-only validation: 114 held-out predictions')
    for ax in axes:
        ax.grid(axis='y', color='#e4e7ea'); ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
    fig.suptitle('First xG extension: test the value of shot angle', fontsize=21, weight='bold', y=0.96)
    fig.text(0.5, 0.85, 'Both teams’ non-penalty shots in seven England 2019 World Cup fixtures\nCandidate selection: one held-out fixture at a time inside the first five games; scaling fit on each fitting subset only', ha='center', fontsize=11)
    fig.text(0.5, 0.055, 'Left points are geometric examples, not observed shots · 105x68 reference dimensions are assumed, not venue measurements.\nOnly 150 selected shots; final two games were already inspected in lesson 18. No production-model or general performance claim.\nSource: StatsBomb Open Data · Geometry foundation: Soccermatics Lesson 2', ha='center', fontsize=9)
    path = ROOT / 'figures/28_shot_angle_model_comparison.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/25_shot_angle_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print('Selected by training-only log loss:', evidence['selected_candidate'])
    for name, candidate in evidence['candidates'].items():
        print(name, 'CV:', candidate['validation_metrics'], 'Reused check:', candidate['reused_test_metrics'])
    print('Saved:', path)
    plot_evidence(evidence)


if __name__ == '__main__':
    main()
