# Football analysis learning journal

Updated: 28 October 2026

## Goal

Become a football analyst who can ask useful football questions, analyse event data,
explain findings and limitations, and defend a reproducible portfolio project.
The working environment is Python in Spyder.

## How we will work

Each lesson should record:

1. **Question:** What do we want to understand about football?
2. **Method:** Which matches, events, filters, and calculations answer it?
3. **Evidence:** Which script and figure reproduce the result?
4. **Interpretation:** What can we say, and what remains uncertain?
5. **Independent practice:** A small calculation, explanation, or code change by the learner.

Worked examples are documented as guided work. Reading an explanation or asking to
continue does not demonstrate independent understanding. Practice attempts and
feedback should be recorded separately.

## Current project

**England vs Sweden, 6 July 2019, Women's World Cup.** StatsBomb match ID 69301;
competition 72, season 30. Source data is downloaded through `mplsoccer.Sbopen`.
This is a guided learning project following Soccermatics, with explicitly labelled
extensions. A portfolio version should credit the course, data provider, and assistance.

### Passing network: who connected?

- Script: `03_passing_network.py`.
- Scope: England completed passes before England's first substitution at 49:23,
  excluding throw-ins; the cutoff uses event order.
- Result: 220 completed passes. Bronze -> Parris: 9; Parris -> Bronze: 7;
  combined connection: 16. McManus–Greenwood: 20 combined.
- Circle location: mean of the player's pass-start and reception locations.
- Circle area: completed passes made. Line width: combined pass count for a pair.
- Display filter: a pair needs at least three passes to receive a line.
- Course centralisation score: 0.070, based on all 220 passes, not only visible links.
- Limit: average event locations are not tracking positions; frequency is not quality.

### Forward passing: direction and denominator

- Scripts: `04_forward_passing_network.py`, `05_forward_pass_success.py`.
- Same time window and throw-in exclusion. Forward means `end_x > x`.
- 124 of the 220 completed passes went forward: 56.4%.
- Bronze's forward share among completions: 20 / 32 × 100 = 62.5%.
- Bronze's forward-pass success rate among attempts with known outcomes:
  20 / 29 × 100 = 69.0% (20 completed, nine unsuccessful).
- Two England forward attempts with Unknown outcomes are excluded from success rates.
- Limit: forward does not automatically mean progressive or dangerous. Player roles
  and pass difficulty matter when comparing players.

### Heatmaps: where did passes start?

- Script: `06_pass_heatmap.py`.
- The 220 completed pass starts are counted in a grid of six columns and five rows.
- Each cell covers 20 x-coordinate units and 16 y-coordinate units.
- All cell counts sum to 220. Labels are counts, not percentages or shot totals.
- Limit: a dark area indicates frequent pass starts, not necessarily attacking value.

### Passes shortly before shots: add possession and timing

- Selection: `07_passes_before_shots.py`; arrows: `08_plot_passes_before_shots.py`;
  heatmap: `09_passes_before_shots_heatmap.py`.
- Start with completed passes made by the possession team. Exclude Throw-in, Corner,
  Free Kick, Kick Off, and Goal Kick, following the tutorial's listed filters.
- Match passes to England shots in the same match, half, and recorded possession.
- Require the pass to precede the shot in event order and be within 0–15 seconds.
- Count each pass once, using its nearest upcoming qualifying shot.
- Before the first substitution: 204 eligible passes; nine qualify before three shots.
- Concrete example: White passes at 22:40; Bronze shoots at 22:46 in the same
  possession. The six-second gap qualifies.
- Limit: this time-window rule does not establish causation, assists, or pass quality.

### Expand the time period

- Script: `10_full_match_passes_before_shots.py`.
- Change: include both halves and added time; retain the other selection rules.
- Full match: 403 eligible completed passes; 11 England shots; 18 qualifying passes
  associated with six shots. The earlier nine pass IDs remain included.
- Figure: `figures/13_england_full_match_passes_before_shots_heatmap.png`.
- The highest cell count is four pass starts. All cell counts sum to 18.
- Interpretation: more playing time gives us more observations. The increase from
  nine to 18 does not by itself show improved performance. One match is insufficient
  to establish a general team pattern.

### Across the tournament: counts per team game

- Date: 27 October 2026. Script: `11_tournament_passes_per_game.py`.
- Question: Where did England's qualifying passes start across their 2019 World Cup,
  expressed as an average per team game?
- Scope: all seven England matches, 9 June–6 July 2019, full match periods.
- Method: same completed possession-team pass, restart exclusion, same-half/possession,
  0–15-second window and pass-deduplication rules as the full-match example.
- Per-match qualifying counts, chronologically: Scotland 37, Argentina 35, Japan 40,
  Cameroon 20, Norway 38, United States 12, Sweden 18.
- Total: 200. Average: 200 / 7 = 28.57 qualifying passes per team game.
- Each heatmap cell is its raw pass-start count divided by all seven team games,
  including games with zero starts in that cell. Busiest cell: 21 / 7 = 3.0.
- Figure: `figures/14_england_tournament_passes_before_shots_per_game.png`.
- Evidence: `data/11_tournament_passes_evidence.json` preserves selected pass IDs,
  match counts, raw zone counts and exact rates; displayed labels use one decimal.
- Checks: seven distinct matches loaded, event IDs unique within matches, Sweden
  reproduces 18, all raw zone counts sum to 200, exact zone rates sum to 200 / 7.
- Interpretation: this is a tournament average, not a promise for each game. A score
  of 3.0 means three pass starts per game on average, not three shots or 3%.
- Limits: per game does not adjust for possession, opponents, game state, pass difficulty
  or player minutes. This remains guided work; interpretation needs learner practice.
- Practice: a zone has 14 qualifying pass starts across seven games. Calculate its
  average per game, then explain the unit in words.

### Which players made the qualifying passes?

- Date: 27 October 2026. Script: `12_players_passes_before_shots.py`.
- Reuses the 200 selected tournament passes saved by script 11; no selection rules changed.
- Group by passer, count selected passes, divide by all seven England team games.
- Bronze: 28 total, 4.00 per team game; Kirby: 24, 3.43; Scott and Parris: 19 each,
  2.71 each. These are counts within the 200-pass selection, not all their passes.
- All 18 passers' totals reconcile to 200. The figure displays the top ten only.
- Figure: `figures/15_england_players_passes_before_shots.png`.
- Interpretation: Bronze made the largest number of qualifying passes in this selection.
  This does not establish that she was England's best passer.
- Limitation: the shared denominator of seven team games does not adjust for player
  appearances, minutes, role, or pass difficulty. Dividing all players by seven also
  leaves their ordering by total unchanged. Comparing rates per 90 requires minutes.
- Practice: explain why unequal playing time matters before judging two players.

### Playing-time adjustment and the xG challenge

- Date: 27 October 2026. Script: `13_minutes_and_shot_quality.py`.
- Question: How do player comparisons change after adjusting for minutes and
  restricting the following shot to xG strictly greater than 0.07?
- Playing time: reconstruct registered player intervals from Starting XI,
  substitutions, sending-offs/permanent departures and Half End timestamps. Sum
  elapsed halves, including added time and excluding halftime. Retain temporary
  injury absences in registered playing time; this differs from an exact tracking-based
  time-on-pitch measure and some standard minute conventions.
- The method accounts for Bright's second-yellow dismissal against the USA.
  Each match's player-time total reconciles to eleven full-match durations minus
  time lost to sending-offs/permanent departures. Eligible passes fall within their
  passers' reconstructed intervals. Players with zero qualifying passes retain minutes.
- Per 90 = selected pass count / reconstructed minutes × 90.
- Bronze: 28 passes / 691.18 minutes × 90 = 3.65 per 90.
- Kirby: 24 / 497.11 × 90 = 4.35 per 90. Their ordering changes from the raw totals.
- Course challenge: filter eligible shots to xG > 0.07 BEFORE selecting passes.
  Match by possession/half, require 0–15 seconds and event order, then deduplicate
  each pass against its next qualifying shot. Filtering an already-deduplicated
  nearest-shot result could miss a pass that also precedes a later higher-xG shot.
- Results: 200 original pass IDs reproduced exactly; 113 unique passes qualify
  before above-threshold shots. These 113 are a subset of the original 200.
- Above-threshold counts/rates: Bronze 15, 1.95 per 90; Kirby 13, 2.35 per 90;
  Walsh 11, 2.22 per 90. xG belongs to the shot, not the pass.
- Figure: `figures/16_england_passes_per90_shot_quality.png`. It displays outfield
  players with at least 270 reconstructed minutes, a disclosed teaching display rule,
  not a universal statistical reliability threshold. All player results remain in evidence.
- Example of excluded exposure: Daly has 11 passes in 212.20 minutes (4.67 per 90),
  but falls below the chart's selected minimum. A minimum-minute filter changes
  who appears in the chart; it does not establish who is best.
- Evidence: `data/13_minutes_and_quality_evidence.json` retains player intervals,
  match-time audits, both selected-pass sets, shot xG and rates. Raw event cache
  at `data/cache_2019_events/` supports rerunning without repeat downloads.
- Provisional observation: Kirby recorded a higher frequency of involvement before
  shots per reconstructed 90 than Bronze in this tournament, despite fewer total
  selected passes. This remains descriptive; roles, pass difficulty, game state and
  possession differ. Review event sequences before making a scouting recommendation.
- Interpretation limits: xG > 0.07 is the course exercise's chosen cutoff, not a universal
  definition of a good chance. Per-90 rates do not remove all opportunity differences.
  Multiple passes may be credited before one shot, so these are not assist totals
  or independent chances created. Do not sum associated shot xG as player-created xG.
- Practice: write a short analyst paragraph comparing Bronze and Kirby using total,
  minutes, per-90 and above-threshold rate; separate observations from a conclusion
  about overall player quality. Then change MIN_MINUTES or XG_THRESHOLD in Spyder
  and explain which interpretation changes. No further arithmetic-only quiz.

### Threshold sensitivity and a spatial player profile

- Date: 28 October 2026. Scripts: `14_threshold_sensitivity.py` and
  `15_kirby_passing_profile.py`. User requested faster grouped lessons and practical
  project work; the assistant performed the threshold exercise as requested.
- At xG > 0.10 the selection contains 98 passes, versus 113 at xG > 0.07.
  The strict 0.10 pass IDs are a subset of the 0.07 selection. The original
  0.07 evidence is preserved rather than overwritten.
- Kirby: 13 -> 12 passes, 2.35 -> 2.17 per 90. Bronze: 15 -> 11,
  1.95 -> 1.43. Walsh: 11 -> 9, 2.22 -> 1.82. Parris retains all 12,
  1.95 per 90. Player order changes; Kirby remains highest among displayed
  outfield players with at least 270 reconstructed minutes.
- This is sensitivity analysis: test whether a conclusion depends on a chosen
  definition. It does not establish statistical significance or universal robustness.
- Next lesson applied the rate to a spatial profile of Kirby, chosen in the
  preceding lesson: 12 selected passes across four matches, 10 forward and two
  backward. Nine started already inside the final third; only two entered it
  from outside. Entries require x < 80 and end_x >= 80.
- Figure 17 compares thresholds. Figure 18 shows individual pass starts/endpoints
  and a heatmap of the same starts. Gold arrows identify final-third entries.
  All map counts sum to 12; unrelated and unsuccessful passes are omitted.
- Correct interpretation: the selected sample describes frequent involvement
  within attacking areas; it does not establish Kirby's full passing style or
  overall superiority. Review omitted passes, roles, game context and sequences.
- Evidence: `data/14_threshold_sensitivity_evidence.json` and
  `data/15_kirby_profile_evidence.json`. Figures inspected for readable labels.
- Added `PROJECT_BRIEF.md` with the case-study question, deliverables, reproduction
  steps, limitations and wider learning path. Portfolio remains guided/in progress.
- Applied practice for later: a five-sentence assessment connecting rates, spatial
  evidence, sensitivity, limitations and a follow-up investigation. Do not claim
  independent mastery from assistant-executed tasks.

### Portfolio documentation and Git preparation

- Date: 28 October 2026. User requested a research portfolio suitable for résumé presentation.
- Rewrote the project README for a recruiter/coach; retained the old guide in
  `docs/LEARNING_GUIDE.md`. Added case study, methods, reproduction notes and accurate
  in-progress résumé wording. Added source attribution and provider logo.
- Added an input-hash manifest, saved-evidence checks, a CI workflow and direct
  dependency pins. Cache and virtual environments are excluded from Git.
- Evidence checks passed locally and without the raw cache. Dependency resolution
  dry run passed; no new clean-environment installation is claimed.
- Local Git repository initialized and project committed. GitHub visibility is still
  to be chosen before publication. No public project URL is claimed yet.
- This improves presentation and inspectability, not evidence of independently
  mastered methods. Independent reproduction and explanation remain part of learning.

## Evidence of learning

- Demonstrated in conversation: 6 out of 10 = 60%; 14 qualifying passes across seven games = two per game.
- Correctly described the heatmap as passes from an area within 15 seconds before a shot;
  feedback reinforced the units per game, completed passes, start locations and same possession.
- Earlier recorded practice: identifying the higher individual-shot xG and adding
  two simple xG values.
- Covered with assistance, still to practise independently: denominator selection,
  possession matching, reading pitch plots, explaining limitations, and changing filters.
- Current scripts and figures were prepared and executed with assistant support.

## Reflection practice still pending

Write three sentences in your own words:

1. What question does the full-match heatmap answer?
2. What does the number four in its darkest cell mean?
3. What does this figure **not** tell a coach?

Then rerun script 10 in Spyder and locate the line that keeps passes within
15 seconds before a shot. A later exercise will change this window and compare results.

The seven-match extension has now been completed with guidance. Review the practice
above before treating interpretation and denominator selection as independently learned.

## Sources

- [StatsBomb Open Data](https://github.com/statsbomb/open-data)
- [Soccermatics: passing networks](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html)
- [Soccermatics: pass heat maps](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html)

Live data updates may change reproduced results; the values above record our current runs.
