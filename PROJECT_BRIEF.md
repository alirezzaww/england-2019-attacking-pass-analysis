# Practical project: England's attacking passing involvement

## Purpose and audience

Produce a reproducible player-analysis case study for a coach or performance analyst:
**Which England players were frequently involved in passing shortly before shots at
the 2019 Women's World Cup, and how does that picture change with playing time,
shot-quality thresholds, and spatial context?**

This is a guided portfolio project in progress. It uses public event data and does not
constitute a recruitment recommendation or a complete assessment of any player.

## Current evidence

- Seven England matches, 9 June–6 July 2019; StatsBomb competition 72, season 30.
- 200 completed possession-team passes within 0–15 seconds before an England shot
  in the same half and possession, excluding listed restarts. Each pass counted once.
- Per-90 denominators reconstructed from starts, substitutions, dismissals and half
  endings. Added time included; halftime excluded; temporary injury absences retained.
- Shot-xG thresholds: strictly above 0.07 retains 113 passes; above 0.10 retains 98.
- At 0.10, Kirby has 12 qualifying passes and 2.17 per reconstructed 90. Bronze has
  11 and 1.43. Kirby has the highest rate among outfield players meeting the chosen
  270-minute display minimum. This does not identify the best passer overall.
- Kirby profile: 10 forward, two backward; nine starts already inside the final third;
  two entries from outside it. These 12 passes occurred across four of the seven games.

## Deliverables and status

1. **Implemented with guidance:** data acquisition, event filters, shot/pass matching,
   checks, per-game heatmaps, player counts and reconstructed playing time.
2. **Implemented with guidance:** per-90 comparisons and a 0.07 vs 0.10 sensitivity
   check, preserving both selections for inspection.
3. **Implemented with guidance:** Kirby's individual pass map, start-zone counts and
   final-third-entry definition.
4. **Match variation and passing-volume comparison implemented with guidance. Still to develop:** comparisons
   within roles, opportunity/context adjustments, statistical uncertainty, and review of individual
   sequences in video when video is available.
5. **Written with guidance; independent defence still to practise:** a concise
   case study in `docs/CASE_STUDY.md`, with observations, limitations and follow-up
   questions supported by the existing scripts and figures.

## Reproduce the current player-analysis block in Spyder

Use the existing project interpreter `venv/bin/python`.

- Run `11_tournament_passes_per_game.py` to create the saved tournament selection.
- Run `13_minutes_and_shot_quality.py` to reconstruct time and create the baseline.
- Run `14_threshold_sensitivity.py` to compare 0.07 and 0.10 without overwriting
  the 0.07 baseline.
- Run `15_kirby_passing_profile.py` to inspect the 0.10 Kirby selection.

Scripts 11 and 13 require internet access for missing source data. Script 13 caches
raw events in `data/cache_2019_events/`; scripts 14 and 15 use local evidence/cache.
JSON files in `data/` retain selected event IDs, match counts, rates and time audits.

## Definitions that the assessment must preserve

- A pass before a shot is not necessarily the final pass, an assist, or a cause of it.
- xG describes the associated shot; do not assign it to the pass as a modelled pass value.
- A final-third start has `x >= 80`. A final-third entry has `x < 80` and `end_x >= 80`.
- Per-game and per-90 rates have different denominators. Neither controls for role,
  team possession, scoreline or pass difficulty.
- Multiple passes can precede the same shot. Do not count them as independent chances
  or sum their associated shot xG to claim player-created xG.
- Threshold sensitivity is a robustness check, not a significance test.
- Twelve selected passes cannot establish a general player style; this map omits all
  other passes and unsuccessful attempts.

## Practical analyst exercise

Use the code and figures to write a five-sentence assessment of Kirby. Include one
rate, one spatial observation, one definition-sensitive finding, one limitation and
one concrete follow-up investigation. Avoid an overall player-quality ranking.

## Wider learning path

Build the following skills through this and later projects: Python/pandas and data
quality; football event definitions and tactics; exploratory analysis and visualisation;
fair comparison and statistical uncertainty; xG modelling and validation; action-value
models such as xT; scouting and recruitment questions; clear reporting, reproducibility
and version control. Progress will be judged through applied work, not only quizzes.

## Sources and attribution

- [StatsBomb Open Data](https://github.com/statsbomb/open-data)
- [Soccermatics: pass heat maps](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html)
- [Learning journal](LEARNING_JOURNAL.md)

Prepared with assistant support; distinguish guided work from independently reproduced
and explained work when presenting the portfolio.

## Educational modelling extension

Lesson 18 begins the modelling learning path with a distance-only logistic xG model,
114 training shots and 36 held-out shots. This separate exercise does not replace
StatsBomb xG in the passing study. It demonstrates a binary target, train/test
separation, baseline comparison and probability-error metrics; it is not a validated
production model. General uncertainty and opportunity adjustment remain future work.

## Latest passing extension: time-window sensitivity

Lesson 19 now tests 5-, 10- and 15-second windows at fixed shot xG > 0.10. Counts are
38, 68 and 98. Walsh versus Bronze changes rate ordering between 5 and 15 seconds.
The implementation preserves selected IDs and constant playing-time denominators,
with independent cached-event reconstruction checks. See
[the report](reports/02_time_window_sensitivity.md) and
[the practical lesson](lessons/0001-time-window-sensitivity.html).
