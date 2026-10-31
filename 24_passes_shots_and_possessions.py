"""Lesson 24: distinguish selected passes, assigned shots and possessions.

Inspect the 12 qualifying passes made while England trailed in lesson 22.
Shot xG is counted once per distinct assigned shot, never once per preceding pass.
This is a measurement audit and event inspection, not a pass-value model.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def group_assigned_shots(passes):
    """Group by match + assigned shot, rejecting duplicate passes or inconsistent links."""
    groups, seen = {}, set()
    for row in passes:
        identity = (row['match_id'], row['id'])
        if identity in seen:
            raise ValueError('A selected pass appears more than once')
        seen.add(identity)
        key = (row['match_id'], row['shot_id'])
        bucket = groups.setdefault(key, [])
        if bucket and any(row[field] != bucket[0][field] for field in ['shot_xg', 'period', 'possession']):
            raise ValueError('Passes linked to the same shot disagree about shot or possession metadata')
        bucket.append(row)
    return groups


def summarize_units(passes):
    groups = group_assigned_shots(passes)
    return {'qualifying_passes': len(passes), 'distinct_assigned_shots': len(groups),
            'distinct_possessions': len({(p['match_id'], p['period'], p['possession']) for p in passes}),
            'assigned_shot_xg_counted_once': sum(rows[0]['shot_xg'] for rows in groups.values()),
            'incorrect_repeated_shot_xg_sum_for_demonstration': sum(p['shot_xg'] for p in passes)}


def build_evidence():
    high = json.loads((ROOT / 'data/14_threshold_sensitivity_evidence.json').read_text())['selected_passes']['0.10']
    context = json.loads((ROOT / 'data/22_score_state_evidence.json').read_text())
    trailing_ids = {(p['match_id'], p['id']) for p in context['passes'] if p['state'] == 'Trailing' and p['qualifying']}
    selected = [p for p in high if (p['match_id'], p['id']) in trailing_ids]
    assert {(p['match_id'], p['id']) for p in selected} == trailing_ids
    audits = {a['match_id']: a for a in context['match_audits']}
    raw_events = {m: json.loads((ROOT / f'data/cache_2019_events/{m}.json').read_text())
                  for m in {p['match_id'] for p in selected}}
    groups = []
    for (match_id, shot_id), rows in group_assigned_shots(selected).items():
        shot = next(e for e in raw_events[match_id] if e['id'] == shot_id)
        assert shot['type']['name'] == 'Shot' and shot['team']['name'] == "England Women's"
        assert shot['shot']['statsbomb_xg'] == rows[0]['shot_xg'] > 0.10
        for row in rows:
            assert row['period'] == shot['period'] and row['possession'] == shot['possession']
            assert row['index'] < shot['index']
            gap = shot['minute'] * 60 + shot['second'] - row['clock']
            assert 0 <= gap == row['seconds_before_shot'] <= 15
        prior_goals = [g for g in audits[match_id]['goals'] if g['index'] < shot['index']]
        score = prior_goals[-1]['score_after'] if prior_goals else [0, 0]
        groups.append({'match_id': match_id, 'opponent': audits[match_id]['opponent'],
                       'shot': {'id': shot_id, 'index': shot['index'], 'period': shot['period'],
                                'possession': shot['possession'], 'minute': shot['minute'], 'second': shot['second'],
                                'player_name': shot['player']['name'], 'xg': shot['shot']['statsbomb_xg'],
                                'outcome': shot['shot']['outcome']['name'],
                                'score_before_england_opponent': score},
                       'selected_passes': sorted(rows, key=lambda p: p['index'])})
    groups.sort(key=lambda g: (g['match_id'], g['shot']['index']))
    summary = summarize_units(selected)
    summary['goals_from_represented_shots'] = sum(g['shot']['outcome'] == 'Goal' for g in groups)
    return {'sources': ['14_threshold_sensitivity_evidence.json', '22_score_state_evidence.json'],
            'scope': 'Selected passes made while England trailed; all eligible starting locations',
            'time_window_seconds_inclusive': 15, 'xg_threshold_strictly_greater_than': 0.10,
            'summary': summary, 'groups': groups,
            'interpretation_limit': 'Only assigned shots represented by selected passes, not all shots while trailing; no pass-created xG or causal credit'}


def plot_sequences(evidence):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(evidence['groups']), 1, figsize=(13, 8))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.21, hspace=0.85)
    for ax, group in zip(axes, evidence['groups']):
        shot = group['shot']
        opponent = {"United States Women's": 'USA', "Sweden Women's": 'Sweden'}.get(group['opponent'], group['opponent'])
        ax.hlines(0, -15, 0, color='#b9c7ce', linewidth=2)
        for j, row in enumerate(group['selected_passes']):
            x = -row['seconds_before_shot']
            ax.scatter(x, 0, color='#24658a', s=65, zorder=3)
            y = 0.24 if j % 2 == 0 else -0.30
            ax.annotate(f"{row['player_name'].split()[-1]}\n{row['seconds_before_shot']} sec before",
                        xy=(x, 0), xytext=(x, y), ha='center', va='center', fontsize=9,
                        arrowprops={'arrowstyle': '-', 'color': '#687e8c'})
        ax.scatter(0, 0, marker='*', color='#b77516', s=180, zorder=4)
        ax.text(0.5, 0, 'SHOT', va='center', fontsize=10, weight='bold')
        ax.set_xlim(-16, 2.4); ax.set_ylim(-0.65, 0.65); ax.set_yticks([])
        ax.set_xticks([-15, -10, -5, 0])
        ax.set_title(f"England v {opponent} | {shot['minute']:02d}:{shot['second']:02d} | "
                     f"{shot['player_name']} | {shot['outcome']} | shot xG {shot['xg']:.3f}", fontsize=11, loc='left', pad=10)
        for side in ['top', 'right', 'left']:
            ax.spines[side].set_visible(False)
    axes[-1].set_xlabel('Seconds relative to the assigned shot (shot = 0)')
    fig.suptitle('12 selected passes represent 3 assigned shots', fontsize=21, weight='bold', y=0.96)
    fig.text(0.5, 0.875, 'England while trailing against USA and Sweden · 2019 Women’s World Cup\nEach row shows four selected passes before one shot, within one possession', ha='center', fontsize=11)
    fig.text(0.5, 0.045, 'Blue circles = selected completed passes; gold star = assigned shot · Other actions and passes may occur between shown events.\nOnly shots represented by these selected passes are shown; this is not every shot while trailing.\nShot xG is a shot estimate, not pass value or causal credit · Source: StatsBomb Open Data', ha='center', fontsize=9)
    path = ROOT / 'figures/27_passes_shots_possessions.png'
    fig.savefig(path, dpi=180, bbox_inches='tight'); print('Saved:', path)
    plt.show()


def main():
    evidence = build_evidence()
    path = ROOT / 'data/24_shot_units_evidence.json'
    path.write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence['summary'], indent=2))
    print('Saved:', path)
    plot_sequences(evidence)


if __name__ == '__main__':
    main()
