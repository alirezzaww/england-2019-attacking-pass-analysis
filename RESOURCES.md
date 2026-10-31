# Football analytics resources

## Knowledge

- [Soccermatics: pass heat maps](https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassHeatMap.html)
  Primary course example for 15-second pass selection, possession matching and duplicate handling.
  Our 5/10/15-second comparison is a project extension, not a copied course lesson.
- [StatsBomb Open Data](https://github.com/hudl/open-data)
  Primary event-data source; use for source schema, competition data and licensing.
- [Soccermatics: fitting an xG model](https://soccermatics.readthedocs.io/en/latest/gallery/lesson2/plot_xGModelFit.html)
  Foundation for the separate educational model in lesson 18; its results do not replace provider xG.

- [SciPy: bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)
  Primary reference for replacement sampling, paired indices and percentile intervals.
  Lesson 21 implements an explicit teaching loop; small-sample coverage remains unvalidated.

- [StatsBomb Open Data specification](https://raw.githubusercontent.com/statsbomb/open-data/master/doc/StatsBomb%20Open%20Data%20Specification%20v1.1.pdf)
  Primary event definitions, including Shot outcomes and own-goal event types; used
  for lesson-22 score reconstruction and its explicit accounting convention.

- [scikit-learn: LeaveOneGroupOut](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.LeaveOneGroupOut.html)
  Primary grouped-validation design reference. Lesson 25 implements fixture-held-out
  folds directly without adding the library as a dependency.
- [scikit-learn: cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)
  Primary reference for fitting preprocessing on the fitting subset before transforming
  held-out rows. Use with the source xG lesson for model-comparison work.

- [scikit-learn: probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
  Primary reference for reliability diagrams and comparison of bin-average probabilities
  with observed positive fractions. Lesson 26 is diagnostic only, with no recalibrator.

## Gaps

Role-specific comparisons, statistical uncertainty, larger-sample model validation and
video review remain future project work. No community participation has been requested.
