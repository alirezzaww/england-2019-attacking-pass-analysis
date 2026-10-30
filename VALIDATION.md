# Validation record

Updated: 30 October 2026.

- Saved-evidence checker passed with all seven cached raw-input hashes verified.
- Checker also passed in a clean temporary directory without the raw cache or
  third-party dependencies.
- Selected pass IDs, 200-pass baseline, 113/98 threshold subsets, player-time totals,
  per-90 rates and Kirby spatial counts reconcile.
- Python source compiled successfully. Local Markdown links and referenced images resolve.
- Installed `requirements-core.txt` successfully into a new Python 3.11 virtual
  environment on macOS. Ran `scripts/run_research.py --headless` in a clean project
  copy without an existing event cache. All stages (11, 13–18) and evidence checks
  completed. All seven regenerated evidence files matched saved results within
  1e-10 numerical tolerance; all seven raw-input hashes verified.
- Analysis stages were executed and charts inspected during the guided project.
- [Initial public GitHub Actions run](https://github.com/alirezzaww/england-2019-attacking-pass-analysis/actions/runs/41046075862)
  passed on Windows, macOS and Ubuntu. It checks saved evidence, website assets/data,
  browser script syntax and Python compilation. It does not install the full plotting
  environment or rerun network-dependent analysis on all three operating systems.
- Browser inspection at phone and desktop widths found no page-wide horizontal
  overflow; all chart images loaded. Selecting xG > 0.07 updated the table to 113
  passes. Moving the distance slider from 15 to 25 changed its estimate from 10.2%
  to 3.1%. This is responsive browser verification, not testing on every physical device.
- Website assets and JSON mirror reconcile with the original figures and research
  evidence. Sites reported a successful public production deployment.

These checks support artifact consistency and inspection. They do not establish
statistical significance, tactical causality or general player quality.

Match-variation evidence now reconciles by fixture against the selected pass IDs and
player intervals, including absence handling, pooled rates and leave-one-out results.

Passing-volume evidence reconciles 98 selected events against 2,837 eligible completed
passes; per-player shares and the volume × share decomposition match per-90 rates.

Lesson 18 executed successfully: optimiser converged; 114/36 match-disjoint split;
training-only scaling and all stored probabilities/test scores reconcile independently.
Figure 21 visually inspected. No external or general model-quality claim is inferred.

## Lesson 19 validation — 30 October 2026

The new time-window script ran successfully in the project environment. The resulting
figure was visually inspected. Counts are 38, 68 and 98 for inclusive 5, 10 and 15
seconds at fixed xG > 0.10. The evidence checker reconciles every selected ID, player
count, unchanged minutes and per-90 rate. With the raw cache present, it independently
reconstructs all three selections from all seven matches. The 15-second set equals
the existing 98-pass selection. Python compilation, website mirror checks and local
link checks pass. This extension does not rerun or alter the educational xG model.

## Lesson 20 validation — 30 October 2026

The new script executed successfully in the project environment and figure 23 was
visually inspected. All 2,837 eligible event IDs and starting locations reconcile to
cached raw inputs across seven matches; the selected subset is exactly the original
98 events. Per-player totals match lesson 17. Three offline unit tests cover zone
boundaries/invalid coordinates, missing denominators versus measured zero, and
pooled counts versus an unweighted mean. Saved-evidence checks validate every zone,
count, percentage and empty cell. Full CI results are available under the repository's
Actions tab for the published commit; local checks alone do not imply remote success.
