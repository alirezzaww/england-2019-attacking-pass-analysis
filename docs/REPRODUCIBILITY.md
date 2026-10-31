# Reproduce and inspect the analysis

## Setup on Windows, macOS or Linux

Install Python 3.11 and Git, then clone the public repository:

```bash
git clone https://github.com/alirezzaww/england-2019-attacking-pass-analysis.git
cd england-2019-attacking-pass-analysis
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
```

On Windows PowerShell (activation is optional):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe scripts/run_research.py --headless
```

On macOS/Linux with the environment activated:

```bash
python scripts/run_research.py --headless
```

For interactive plotting omit `--headless`. For Spyder, select this environment's
Python interpreter and run each numbered lesson file. Install a `spyder-kernels`
version compatible with your Spyder release into that environment if needed.
Avoid installing all notebook/IDE extras merely to run the research.

## Environment and execution

The executed local interpreter is Python 3.11.4. `requirements-core.txt` pins the six
direct analysis dependencies observed there. `requirements.txt` also records the
earlier notebook/Spyder dependencies. An external Spyder interpreter needs a compatible
`spyder-kernels` release; the analysis libraries alone do not provide that kernel.

From the project root with the environment activated:

```bash
python 11_tournament_passes_per_game.py
python 13_minutes_and_shot_quality.py
python 14_threshold_sensitivity.py
python 15_kirby_passing_profile.py
python 16_match_variation.py
python 17_passing_volume_adjustment.py
python 18_first_xg_model.py
python 19_time_window_sensitivity.py
python 20_pass_location_context.py
python 21_match_bootstrap_uncertainty.py
python 22_score_state_context.py
python 23_within_match_score_comparison.py
python 24_passes_shots_and_possessions.py
python 25_shot_angle_model.py
python 26_probability_calibration.py
python scripts/check_evidence.py
```

Prefix plotting commands with `MPLBACKEND=Agg` for a headless terminal. Figures save
without an interactive window; `plt.show()` can emit a noninteractive-backend warning.

Script 11 downloads match events with mplsoccer. Script 13 reads/downloads raw events
into `data/cache_2019_events/` and uses script 11's saved baseline. Scripts 14 and 15
use local evidence and cached events. Raw cache files are excluded from Git.

## Inspectable evidence

- `11_tournament_passes_evidence.json`: matches, selected IDs, counts and grid.
- `13_minutes_and_quality_evidence.json`: playing intervals, audits and rates.
- `14_threshold_sensitivity_evidence.json`: both threshold selections.
- `15_kirby_profile_evidence.json`: selected player events and spatial totals.
- `16_match_variation_evidence.json`: match counts, minutes, rates and leave-one-out sensitivity.
- `17_passing_volume_evidence.json`: player denominators and qualifying share of completed passes.
- `source_manifest.json`: raw-input file names, source URLs and SHA-256 digests.

These files are in `data/`. Source data is live and can change. Compare new raw
inputs with the manifest and investigate differences before updating results. A hash
identifies captured content; it is not a retrospectively inferred Git source revision.

## Verification scope

The standard-library evidence checker reconciles artifacts, IDs, counts, denominators,
subset relations, rates and spatial totals. It also checks raw hashes when the cache
is present. CI checks saved evidence and Python syntax; it does not redownload and
rerun the full pipeline. Pipeline stages were run and figures visually inspected in
the guided project. See `VALIDATION.md` for the current validation record, including
fresh-environment installation status. Artifact consistency alone does not establish
statistical or tactical validity.

## Educational xG extension

Run `18_first_xg_model.py` after lesson 13 creates the raw event cache. SciPy 1.17.1
is now an explicit direct dependency. The model uses both teams' non-penalty shots,
not the passing selection. Evidence is saved in `data/18_first_xg_model_evidence.json`.
Split IDs, training-only scaling, coefficients, predictions and test metrics are
stored. The checker recomputes these relationships without fitting the model.
The training process itself was executed successfully in the existing environment.

## Time-window extension

Lesson 19 reads saved lesson-14 evidence and produces
`data/19_time_window_evidence.json` and `figures/22_time_window_sensitivity.png`.
It does not require the raw cache to run. The evidence checker independently checks
all three windows against cached raw events when those inputs are present.

## Starting-third extension

Lesson 20 requires lesson 13's raw cache, reads the unchanged lesson-14 selected IDs,
and creates `data/20_pass_location_evidence.json` plus figure 23. Run
`python -m unittest discover -s tests -v` for offline boundary/denominator tests.
The saved-evidence checker needs no plotting dependencies and independently reconstructs
location denominators from raw inputs when available.

## Match-bootstrap extension

Lesson 21 reads saved lesson-20 evidence without downloading data, and creates
`data/21_match_bootstrap_evidence.json` plus figure 24. Python's RNG algorithm,
seed, fixture order, player order, draw count and percentile convention are recorded.
The standard-library checker reconstructs fixture summaries and replays every draw.
Offline unit tests cover paired indices, repeated counts, zero exposure and quantiles.

## Score-state extension

Lesson 22 requires the seven raw event caches. If
`data/cache_2019_events/matches_72_30.json` is absent, it downloads provider match
metadata with a 60-second timeout and caches it outside Git. The saved evidence
records its URL and SHA-256. The score timeline and provider score snapshots are
included in `data/22_score_state_evidence.json`, alongside every tagged pass and
summaries. The evidence checker runs offline without caches; with caches it also
independently reconstructs every pre-pass score and checks the metadata digest.

## Within-fixture comparison

Lesson 23 reads saved lesson-22 evidence without downloading raw data. It creates
`data/23_within_match_evidence.json` and figure 26. The checker rebuilds coverage,
common fixture IDs, numerators, denominators and percentage-point differences from
the saved pass ledger. Unit tests cover zero qualifying counts with valid exposure,
missing overlap and pooling unequal-size fixture groups.

## Shot-unit audit

Lesson 24 reads saved lesson-14 and lesson-22 evidence plus cached raw events for USA
and Sweden; it downloads nothing. It creates `data/24_shot_units_evidence.json` and
figure 27. The checker reconciles selected IDs, assigned-shot groups, possession
identities, times, shot metadata and sums. Without raw caches, saved artifacts still
reconcile; with caches, shot metadata is checked against original events.

## Angle model comparison

Lesson 25 reads saved lesson-18 shots without downloading raw data and uses the
existing NumPy/SciPy dependencies. It creates `data/25_shot_angle_evidence.json` and
figure 28. Folds, feature scaling, coefficients and predictions are preserved. The
standard-library checker recomputes geometry independently, checks fold membership,
means/scales and fitting gradients, and reconciles every prediction, score and
training-only selection. It does not refit models in CI.

## Probability-calibration diagnostic

Lesson 26 reads saved lesson-25 evidence and does not download or refit anything.
It creates `data/26_calibration_evidence.json` and figure 29. The standard-library
checker reconstructs all 114 selected-candidate out-of-fold records, bin memberships,
counts, probabilities and observed rates. Unit tests include boundary values 0 and
1, measured zero versus empty groups and duplicate-shot protection.
