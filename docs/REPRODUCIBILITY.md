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
