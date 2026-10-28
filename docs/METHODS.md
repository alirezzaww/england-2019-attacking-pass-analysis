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
no pass-value model or new xG model is trained.

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
