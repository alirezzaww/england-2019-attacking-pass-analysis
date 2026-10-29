# Validation record

Updated: 29 October 2026.

- Saved-evidence checker passed with all seven cached raw-input hashes verified.
- Checker also passed in a clean temporary directory without the raw cache or
  third-party dependencies.
- Selected pass IDs, 200-pass baseline, 113/98 threshold subsets, player-time totals,
  per-90 rates and Kirby spatial counts reconcile.
- Python source compiled successfully. Local Markdown links and referenced images resolve.
- A pip dependency-resolution dry run using `--ignore-installed` successfully resolved
  `requirements-core.txt` for Python 3.11 on the current macOS host. No fresh virtual
  environment installation or full pipeline rerun was performed during portfolio packaging.
- Analysis stages were executed and charts inspected during the guided project.
- GitHub Actions configuration is included; no remote CI run is claimed before publication.

These checks support artifact consistency and inspection. They do not establish
statistical significance, tactical causality or general player quality.

Match-variation evidence now reconciles by fixture against the selected pass IDs and
player intervals, including absence handling, pooled rates and leave-one-out results.

Passing-volume evidence reconciles 98 selected events against 2,837 eligible completed
passes; per-player shares and the volume × share decomposition match per-90 rates.

Lesson 18 executed successfully: optimiser converged; 114/36 match-disjoint split;
training-only scaling and all stored probabilities/test scores reconcile independently.
Figure 21 visually inspected. No external or general model-quality claim is inferred.
