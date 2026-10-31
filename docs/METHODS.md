# Methods and analytical decisions

## Selection

England Women's, competition 72, season 30, all seven 2019 World Cup fixtures.
Completed passes must be made by the recorded possession team. Excluded pass
subtypes: Throw-in, Corner, Free Kick, Kick Off, Goal Kick. Later passes in a
possession that began with a restart are not automatically excluded.

Match passes to England Shot events by match, period and possession. Require the
pass index to precede the shot index and a 0–15-second gap using recorded minute
and second values. This follows the tutorial's whole-second window convention;
subsecond timestamps are used separately for reconstructed playing time.

Count each pass once against its nearest upcoming eligible shot. For strict
xG > 0.07 or > 0.10, filter shots BEFORE matching/deduplication: a pass can precede
both an earlier lower-xG shot and a later qualifying shot. xG belongs to the shot;
no pass-value model or new xG model is trained for the passing case study.

## Playing time

Starting XI players begin at zero elapsed time. Substitutions close/open intervals;
sending-offs and permanent departures close them. Half End timestamps determine
period durations, combined without halftime. Added time is included; temporary
injury absences remain within registered minutes. This differs from some rounded
match-report conventions and exact tracking-based time on pitch.

Bright's second-yellow dismissal against the USA is accounted for. Each match's
player-time total reconciles to eleven match durations minus time lost to dismissals
or permanent departures. Eligible pass events fall inside their passers' intervals.
Zero-count players retain minutes.

Per game = count / all seven England games, including zeros. Per 90 = player count /
reconstructed minutes × 90. Comparison figures display outfield players with 270+
minutes; all players remain in evidence. This is a presentation choice, not a
reliability guarantee or recruitment criterion.

## Space

StatsBomb's 120 × 80 grid is displayed attacking toward x = 120. Forward means
end_x > x. Final-third starts: x >= 80. Entries: x < 80 and end_x >= 80.
Heatmaps count START locations in a six-column, five-row grid. Profile arrows connect
recorded pass starts and endpoints; they do not trace a curved ball trajectory.

## Match variation

Script 16 uses the same 0.10 selection and reconstructed intervals. All seven
fixtures are shown: a zero with minutes is an observed zero, while no appearance
has no per-90 rate. The pooled tournament rate is sum(counts) / sum(minutes) × 90,
equivalent to a minute-weighted mean of appearance rates. The unweighted mean
answers a different question and is not used as the pooled rate.

Leave-one-appearance-out values are calculated by removing the appearance's count
and minutes together, then recomputing the pooled rate. Their range describes
sensitivity to match inclusion; it is not a confidence interval or significance test.

## Passing-volume denominator

Script 17 counts all completed possession-team passes excluding the same listed
restarts across the seven fixtures (2,837 events). The 98 selected events at
xG > 0.10 must be a subset. For each player, qualifying share = selected passes /
eligible completed passes × 100. An absent denominator would give an undefined
share, not zero. This is not completion rate because failed attempts are not in
the denominator. No general possession or pass-difficulty adjustment is claimed.

A useful identity is selected passes per 90 = eligible passes per 90 × qualifying
share / 100. It decomposes volume and the observed qualifying share; it is not a
causal model. Neither denominator alone ranks overall player quality.

## Checks and limits

Selected IDs, totals, player counts, minutes, rates and spatial counts reconcile.
The original 200-pass selection is reproduced. The 0.10 set is nested in the 0.07
set. The input manifest records raw-event hashes; the saved-evidence checker verifies
artifact consistency, not causal or tactical validity.

Roles, opposition, scoreline, possession and pass difficulty are not adjusted. Seven
matches form a small nonrandom sample; repeated events in an attack are related.
A qualifying pass is not necessarily the final pass, an assist or a cause of a shot.
Multiple passes can share a shot; their associated shot xG must not be summed as
player-created xG. No significance test, validated population confidence interval or overall player ranking
is claimed. Lesson 21 adds an explicitly illustrative match-bootstrap interval.

Primary sources: [StatsBomb Open Data](https://github.com/hudl/open-data) and
[Soccermatics](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html).

## Separate educational distance-only xG model

Lesson 18 uses all Shot events from both teams in the cached seven games, excluding
penalties and shootout periods. Four penalty events are excluded, leaving 150 shots.
The target is 1 for a Goal outcome and 0 otherwise; own-goal event types are outside
this shot sample. Distance to goal centre is sqrt((120-x)^2+(40-y)^2), in standardised
StatsBomb coordinate units, not measured metres on each actual pitch.

The first five chronological matches provide 114 training shots and 11 goals. The
USA and Sweden fixtures provide 36 held-out shots and six goals. No match occurs in
both sets. Distance mean/scale are fit on training only. Two logistic coefficients
(intercept and distance slope) minimise training binary log loss using SciPy BFGS.
The goal label is the training target, never a predictor. Provider xG is unused.

The constant baseline is the training goal rate, 11/114. Both models are evaluated
on the same held-out shots using Brier score and log loss. Lower is better. No
accuracy or AUC claim is substituted for probability evaluation. Test Brier is
0.1315 for the distance model versus 0.1438 for the baseline; log loss is 0.4076
versus 0.4743. Predicted test goals total 2.96 versus six observed goals. The small
sample cannot establish reliable calibration or generalisation.

Headers, shot angle, pressure, defenders, goalkeeper position and other context are
not modelled. The seven fixtures are selected around England, not a representative
population. The fitted curve is shown only over the training distance range; test
predictions can extrapolate. Once a test set has been inspected during development,
repeated tuning against it is not an independent final evaluation. Larger data and
training-only validation are needed for subsequent model selection.

## Time-window sensitivity (lesson 19)

At a fixed shot-xG threshold strictly above 0.10, inclusive windows of 5, 10 and 15
nominal seconds retain 38, 68 and 98 unique passes. All other selection rules and
playing-time denominators remain fixed. The smaller sets are obtained by filtering
the lesson-14 nearest-eligible-shot gaps. Because the nearest eligible shot was
selected after the xG filter, any pass whose nearest eligible shot is outside a shorter
window cannot have another eligible shot inside it. This shortcut is valid for these
shorter windows; it cannot discover extra events beyond the original 15 seconds.

Event IDs are nested and each pass is counted once per setting. Changing the window
alters the numerator and temporal scope, not the player's minutes. This is definition
sensitivity; no statistical interval, independence or causal interpretation is claimed.

## Starting-third context (lesson 20)

Every one of the 2,837 eligible completed passes is assigned using its starting x:
defensive [0,40), middle [40,80), attacking [80,120]. The 98 selected IDs remain unchanged.
Pass-start mix uses the player's full eligible completed-pass count as denominator;
within-zone qualifying share instead uses that player's eligible completed-pass count
in that exact zone. Zero denominators produce null, not zero. All cells reconcile to
lesson 17; the ledger preserves match, event ID, player, start x, zone and selection flag.
The conditional comparison provides broad location context without fully adjusting
role, pass difficulty, pressure or tactical opportunity. No causal effect, confidence
interval or player-quality ranking is inferred.

## Educational paired whole-match bootstrap (lesson 21)

For the attacking-third comparison only, aggregate lesson-20 qualifying and eligible
completed-pass counts by fixture and player. Draw seven fixture indices with replacement
10,000 times using Python `random.Random` seed 20261030. Both players use the same
indices; repeated fixtures repeat both counts. Pool each numerator and denominator
before dividing. The statistic is Kirby share minus Bronze share in percentage points.
Zero-denominator draws are counted as invalid, not zero; intervals use valid draws.
The seeded run has 10,000 valid draws and none invalid.

The observed difference is +7.1475 pp. The illustrative interval is the linear-interpolated
2.5th/97.5th percentiles of the saved differences: −3.1936 to +19.1253 pp. Whole-match
resampling preserves observed within-match grouping; it does not establish independence
or exchangeability between fixtures. Seven selected sequential tournament matches
and sparse numerators limit the method. No validated population coverage, p-value,
probability of superiority, equivalence or causal claim is inferred. The explicit loop
implements the paired percentile idea described in the
[SciPy method documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html),
not its default BCa method.

## Pre-pass score state (lesson 22)

Return to the whole team and all eligible starting locations, retaining the same 2,837
passes and 98 selected IDs. Process each fixture's events in index order from 0–0,
assigning score and state before each pass. Shot/Goal events increment the scoring
team; Own Goal Against increments its opponent, with Own Goal For ignored as a
counterpart. Shootout events are excluded. No own goals occur in these seven inputs.
Final England/opponent scores must match provider match metadata. Its cache path,
source URL and content digest are recorded in lesson-22 evidence; original event
hashes remain in the input manifest.

Leading/drawing/trailing shares are 68/1568, 18/658 and 12/611. Their denominators are
eligible completed passes in the same state, not attempts or minutes. Player and
fixture summaries retain empty cells as null shares. Score is measured immediately
before the pass, not after a following goal or at the final whistle. Trailing occurs
only against USA and Sweden, so score, opponent and other context cannot be separated
by these descriptive comparisons. No causal score effect or general rating is claimed.

## Fixture-overlap check (lesson 23)

Pairwise common fixtures require a positive eligible completed-pass denominator in
both states; a zero selected numerator does not disqualify a fixture. Leading versus
Trailing has no common fixture. Drawing versus Trailing has USA and Sweden. The
restricted pools are 0/120 and 12/611, compared with 18/658 and 12/611 across all seven
fixtures. Within USA the shares are 0/92 and 4/236; within Sweden, 0/28 and 8/375.
An empty common set yields undefined shares and difference, not measured zeros.
This is sample restriction and descriptive within-fixture comparison. Fixture weights
remain proportional to state-specific pass volumes; game phase and other confounding
remain. No causal, equal-weight adjusted or significance claim is made.

## Pass, represented-shot and possession units (lesson 24)

Restrict lesson-14 high-threshold passes by lesson-22 pre-pass Trailing labels. Group
by match and assigned shot ID; count possession identities by match, period and
possession. Twelve selected passes link to three represented shots and three
possessions, with four passes per shot. All three shots are checked against cached
raw event metadata; two outcomes are Goal and one Saved. This is not every team shot
while trailing and not a full action chain. Timeline names are passers, not verified
passer-to-recipient edges. Other actions may occur between selected passes.
The represented-shot xG sum is 0.46052896. The deliberately incorrect per-pass repeated
sum is 1.84211584; it is stored only to illustrate duplication. No pass-created xG,
causal player credit or full team xG claim is made.

## Educational angle candidate and grouped validation (lesson 25)

Retain lesson-18 shot identities, non-penalty exclusions and 114/36 split. Convert x/y
to a 105x68 reference and use a 7.32-wide goal. Distance is to centre; angle is
atan2(7.32*dx, dx² + lateral² - 3.66²). Exact-post geometry is rejected. The reference
is assumed, not a venue measurement. Both new fitted candidates use this distance;
lesson 18's coordinate-unit baseline is not copied unchanged.

Predefine constant, distance and distance+angle candidates. Leave each of the first
five fixtures out once; fit all coefficients, means and scales using the remaining
four. Select by pooled out-of-fold log loss, with Brier secondary. Distance wins
(0.292377 vs 0.300214 for angle); constant scores 0.322997. All fits converge and
likelihood gradients reconcile. Grouped folds are not forward-chaining time forecasts.
Refit all candidates on the 114 training shots, then report the previously inspected
36-shot final-two-fixture check as reused exploratory evaluation. No fresh test,
calibration or general superiority claim is made. Provider xG in the passing study
is unchanged. See [the model report](../reports/08_shot_angle_model_comparison.md).
