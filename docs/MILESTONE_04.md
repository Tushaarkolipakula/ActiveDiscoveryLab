# Milestone 4: revision and physical-data evidence

The learner can now detect inadequate fit after at least two acquired experiments, open a bounded extension library, refit competing equations, and choose another experiment using prediction disagreement. Original candidates remain in competition. Three additional families represent a constant force, a sinusoidal drive with unknown amplitude/phase/frequency, and smooth dry friction. Analytic sensitivity equations accelerate fitting.

This is a finite grammar supplied by the developer, not an LLM generating arbitrary code or unrestricted symbolic discovery. Every extra coefficient incurs a complexity penalty. Noise variance is known in simulation; model-score weights and residual warnings are heuristic. A sinusoidal source starts with the same time origin for every experiment. When one model dominates, structural disagreement can become nearly zero and does not resolve remaining parameter uncertainty.

## Evidence files

- `results/revision-001/plan.json`: predefined five systems and four policies, one seed, four experiments each.
- `results/revision-001/source/`: frozen Python source matching the plan hashes, preserved before UI integration changes.
- `results/revision-001/REPORT.md`: all 20 outcomes, including the out-of-grammar chirp.
- `results/silverbox-001/`: frozen passive physical-data protocol, selected models, metrics and plot.
- `docs/REAL_DATA.md`: measurement provenance, partition boundaries and reproduction steps.

The revision comparison separates fixed-library active selection, always-expanded active selection, adaptive revision with active selection, and adaptive revision with random selection. Compare prediction error, candidate fit count and wall time; more candidate fits do not imply proportional runtime. One seed per mechanism is insufficient for statistical claims.

Silverbox uses an independent discrete-time ARX baseline. It demonstrates real measurement handling and held-out free-running prediction, not physical validation of the active simulator loop. The cubic predictor achieved 4.388 mV and 5.439 mV test RMSE on multisine and full-arrow recordings; the linear predictor achieved 7.708 mV and 15.465 mV. No test outputs beyond the first 50 initialization samples are fed back into predictions.

All 24 automated tests passed after integration, including sensitivity checks, serialization, measurement isolation, numerical integration, and test-output leakage checks. A live revision run and recorded revision replay are also checked in the browser.

## What would justify a stronger future claim

Use new, preregistered systems and multiple noise seeds for replication, calibrate mismatch detection when noise is estimated, address collapsed structural disagreement, and compare against a stronger nonlinear identification baseline. Physical active-learning claims require actual controlled interventions. Existing test results have been inspected and cannot be reused as untouched evidence after tuning.
