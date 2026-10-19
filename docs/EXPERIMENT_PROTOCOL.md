# Development experiment protocol

## Pilot versus final evidence

The four named coefficient settings in benchmark.py are development fixtures. Inspecting results on them is allowed, but they cannot later be relabelled as untouched final-test systems. All current reports are explicitly marked as development pilots.

Before a research claim, freeze a separately generated final system set, noise levels, acquisition settings, primary metric, and analysis plan. Do not tune on that final set. New physical-effect combinations or out-of-family dynamics require a separate generalisation evaluation.

## Controlled comparison

Same candidate library, optimiser budget, noise variance, initial experiment, admissible controls, observation frequency, and experiment count across methods. Use paired noise seeds. Acquisition overhead is included in reported learning time. Evaluation and report rendering are excluded from learning time.

Random and systematic selectors still fit all models after each experiment, allowing like-for-like predictions. The systematic sequence is fixed before observations. Active selection may use past observations only through fitted models. No method may see test errors until its complete run has ended.

## Metrics

- Primary: RMSE over 12 unseen trajectories, divided by RMS ground-truth position over those trajectories (NRMSE).
- Secondary: exact candidate structure match; coefficient L2 error; learning wall time.
- Plot every experiment prefix, including the identical initial experiment.
- Structure identity is a limited syntactic measure. Near-zero extra coefficients and equivalent physical behaviour must be discussed separately.
- Coefficient L2 mixes parameters with different physical units and is diagnostic only; do not use it as the primary ranking.

Final evaluation should expand test trajectories and report paired differences and uncertainty across independently sampled systems and seeds. Current pilot plots show individual curves and their mean, not confidence intervals. They do not support a statistical superiority claim.

## Checks before expanding

- Numerical forward model matches an analytic oscillator.
- Low-noise fitting recovers known linear coefficients.
- Seeds reproduce observations.
- Control limits and budgets are respected.
- The active selector prefers a discriminating intervention in a constructed example.
- Discovery accepts a measurement-only API and produces no test metrics itself.
- Each run records complete data and package/source provenance.

## Failure questions

Does active selection underperform because of early overconfidence, local minima, inadequate model family, or a strong systematic baseline? Does disagreement collapse after model weights concentrate? Do nonlinear coefficients become identifiable only at boundary controls? Preserve all outcomes, including negative results.
