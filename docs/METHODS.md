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
player-created xG. No significance test, confidence interval or overall player ranking
is claimed.

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
