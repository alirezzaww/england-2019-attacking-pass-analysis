# Who was involved in England's passing shortly before shots?

**Alireza Erfanian · Applied football analysis · Guided project in progress**

## Question

How do player comparisons change when total passing involvement before shots is
adjusted for playing time, shot-quality thresholds and spatial context? The intended
audience is a coach or analyst seeking leads for further sequence review.

## Scope

Seven England fixtures, 9 June–6 July 2019. A qualifying event is a completed
possession-team pass within 0–15 seconds before an England shot in the same match,
half and possession. Listed restart types are excluded. Each pass counts once.
Filter shots before matching and deduplicating passes. [Methods](METHODS.md).

## Finding 1: volume and rate answer different questions

Bronze made 28 of the 200 selected passes; Kirby made 24. Their reconstructed
per-90 rates were 3.65 and 4.35 respectively. Bronze contributed more in total;
Kirby contributed more frequently per unit of playing time on this measure.
Differences in role, opportunities and pass difficulty remain unadjusted.

## Finding 2: analytical definitions affect the comparison

The xG > 0.07 selection contains 113 passes; xG > 0.10 contains 98. Kirby's rate
changes from 2.35 to 2.17 per 90; Bronze's from 1.95 to 1.43. Parris retains 12
selected passes, approximately 1.95 per 90 at both thresholds. Some positions change;
Kirby remains highest among displayed outfield players with 270+ reconstructed minutes.
This sensitivity check is not a significance test. The display minimum is not a
statistical guarantee.

![Threshold comparison](../figures/17_england_xg_threshold_sensitivity.png)

## Finding 3: activity inside an area differs from entry into it

Kirby's 12 passes at the 0.10 cutoff contain ten forward and two backward passes.
Nine started inside the final third, while two crossed into it from outside. These
passes occurred across four games. The selected events suggest more involvement
already inside the attacking third than entry into it, within this specific sample.

![Kirby profile](../figures/18_kirby_passes_before_shots_profile.png)

## Provisional analyst observation

Kirby's passing involvement warrants further sequence review. She retained the
highest per-90 rate among displayed players at both tested cutoffs, with most of
her selected passes beginning inside the final third. This does not establish her
full passing style or that she was England's best passer: unrelated and failed
passes are omitted, and player roles and game contexts differ.

## Unresolved questions

Do a few matches drive these results? What changes within comparable roles or after
accounting for possession? Does a larger sample support the pattern? What options,
pressure and tactical purpose are visible in the actual sequences?

Multiple passes can precede one shot; these are not independent chances or assists.
Do not sum associated shot xG as player-created xG. No causal or recruitment claim
is made. [Reproduce and inspect the evidence](REPRODUCIBILITY.md).

Source: [StatsBomb Open Data](https://github.com/hudl/open-data). Course foundation:
[Soccermatics](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html).
Prepared with assistant support; independent reproduction and explanation remain
part of the learning programme.

![StatsBomb](../assets/statsbomb-logo.png)
