# England 2019: attacking passing involvement

**Football analytics portfolio · Python/pandas · In progress**
**Author:** Alireza Erfanian

Which England players were involved in passing shortly before shots at the 2019
Women's World Cup—and how does that picture change with playing time, shot quality
and pitch location?

This applied case study covers seven England matches using StatsBomb Open Data.
It extends a Soccermatics exercise with reconstructed playing time, threshold
sensitivity checks and individual-event inspection. It is a guided learning project
with assistant support, not an independently developed player-valuation model.

## Read the case study

- **[Findings and football interpretation](docs/CASE_STUDY.md)**
- [Methods and definitions](docs/METHODS.md)
- [Reproduce the results](docs/REPRODUCIBILITY.md)
- [Project scope and remaining work](PROJECT_BRIEF.md)

![How the shot-xG threshold changes player rates](figures/17_england_xg_threshold_sensitivity.png)

## Findings from this sample

- **200 qualifying passes** across seven games: completed possession-team passes
  within 15 seconds before a same-possession England shot, excluding listed restarts.
- **113** remain when the following shot must have xG > 0.07; **98** at xG > 0.10.
- At 0.10, Kirby records **2.17 per reconstructed 90** and Bronze **1.43**, from
  12 and 11 passes. Kirby has the highest rate among outfield players meeting the
  chosen 270-minute display minimum.
- Nine of Kirby's 12 selected passes **started inside the final third**, while only
  two **entered it from outside**. Those are different contributions.

These are descriptive findings from a small tournament sample. They do not establish
player superiority, assists, causal chance creation or statistical significance.

## Skills demonstrated by the guided workflow

Event acquisition and filtering; possession/time matching; totals versus rates;
playing-time reconstruction; definition sensitivity; spatial analysis; evidence
reconciliation; reproducible, qualified reporting. The code was prepared with assistance;
the learning journal distinguishes coverage from independent practice.

## Run in Spyder or a terminal

Use Python 3.11. Reuse the existing local environment, or create a new one:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
```

Select that interpreter in Spyder, with a `spyder-kernels` version compatible with
its installed release. Kernel dependencies are separate from the analysis libraries.
From the project root, run:

```bash
python 11_tournament_passes_per_game.py
python 13_minutes_and_shot_quality.py
python 14_threshold_sensitivity.py
python 15_kirby_passing_profile.py
python 16_match_variation.py
python 17_passing_volume_adjustment.py
python scripts/check_evidence.py
```

Stages 11 and 13 require internet for source data. Downloaded raw events are cached
locally and excluded from Git. Saved derived evidence and figures are included.
See [reproduction notes](docs/REPRODUCIBILITY.md) for verification scope and data changes.

## Repository guide

- `01_*.py`–`10_*.py`: foundational guided lessons and single-match analyses.
- `11_*.py`–`17_*.py`: tournament selection, rates, sensitivity, profiles, match variation and passing-volume comparison.
- `figures/`: charts with scope and source captions.
- `data/`: derived evidence and source-input manifest; raw cache is ignored.
- `docs/`: case study, methods, reproduction and résumé presentation.
- `reports/`: earlier England–Sweden shooting assessment.
- `LEARNING_JOURNAL.md`: findings, limitations, practice and progress.

## Status

The descriptive pipeline is implemented. Match variation, weighted rates and qualifying share of completed passes are examined. Role-specific comparison,
opportunity adjustment, statistical uncertainty and video review remain future work.
No new xG model, significance test or finished recruitment recommendation is claimed.

[Learning journal](LEARNING_JOURNAL.md) · [Lesson archive](docs/LEARNING_GUIDE.md)
· [Résumé presentation](docs/RESUME.md)

## Sources and acknowledgement

Data: **[StatsBomb Open Data](https://github.com/hudl/open-data)**, competition 72,
season 30. Source data retains the provider's [licence](https://github.com/hudl/open-data/blob/master/LICENSE.pdf);
this project grants no additional data rights.

![StatsBomb](assets/statsbomb-logo.png)

Foundation: [Soccermatics pass heat maps](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html)
and [passing networks](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html).
Methods and code were adapted and extended with assistant support. xG is supplied
by StatsBomb; no xG model was trained here.
