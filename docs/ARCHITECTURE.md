# Architecture contract — v0.2

## Goal

Identify predictive dynamical models with a limited number of equal-cost interventions. The primary outcome is error on unseen starting conditions versus the number of experiments.

## Data flow

1. Benchmark constructs a measurement callable that closes over private coefficients.
2. Runner calls it with bounded initial position and velocity.
3. Environment returns timestamps and noisy positions only.
4. Fitter returns candidate equations, estimated coefficients, convergence diagnostics, BIC scores, and a regularised local parameter covariance.
5. Selector uses those candidates and the public control bounds to choose an unused experiment.
6. Runner saves each model snapshot and finishes its budget.
7. Evaluator receives the completed snapshots and ground truth, and measures predictions on separate continuous starting conditions.
8. Report reads saved results only.

The callable boundary prevents accidental truth access through normal interfaces; this is not an adversarial security sandbox. Source code necessarily contains benchmark definitions. The discovery algorithm never receives those definitions.

## Explicit assumptions

- Exact initial state controls; observed position in known units.
- Known independent Gaussian sensor noise, stationary across experiments.
- Stable, autonomous, one-dimensional dynamics within a bounded model family.
- All candidate models share the linear restoring/damping terms.
- No unknown forcing, actuator error, sensor drift, or latent dynamics in v0.1.
- Coefficients and units are mass-normalised; separate mass/stiffness recovery is not claimed.

## Design decisions

- Direct trajectory fitting avoids noisy acceleration estimates.
- Four candidate structures make failures interpretable before broad symbolic search.
- Fixed-duration experiments make budget comparisons simple.
- BIC favours simpler explanations; tempered weights soften early elimination but have no calibration guarantee.
- Structural-disagreement acquisition is a baseline, not a new information-theoretic algorithm. The active_local extension adds first-order propagated parameter uncertainty. Both use the same fitted models and weights.
- Static reports precede a dashboard so UI work does not obscure scientific failures.

## Deferred, not implemented

Calibrated parameter posterior estimation; confidence calibration; principled stopping; refusal under non-identifiability; neural selection policies; general symbolic discovery; physical validation. A local covariance heuristic is implemented, but it is not a full posterior and can be inaccurate at parameter bounds or when several fitting modes exist. The learner currently always exports its lowest-BIC candidate, even when all candidates are poor.
