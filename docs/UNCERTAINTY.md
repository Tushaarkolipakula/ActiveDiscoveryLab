# Local parameter uncertainty — v0.2

## Motivation

Structural disagreement vanishes when all candidate weight concentrates on one equation. Its coefficients may nevertheless remain uncertain. A useful experiment could reduce that uncertainty even if no alternative structure is plausible.

## Estimator

Let J be the fitted residual Jacobian, with residuals already divided by the known measurement standard deviation. Let D contain the widths of the allowed coefficient intervals for active terms. Define:

    C = D [(J D)^T (J D) + 12 I]^-1 D

Embed C in a four-by-four matrix with zero rows and columns for absent terms. The 12 I regulariser caps an entirely unobserved parameter direction at the variance associated with a uniform interval in normalised coordinates. It prevents a pseudoinverse from incorrectly assigning zero uncertainty to unidentified directions.

This is a regularised local approximation. It is NOT a calibrated posterior, confidence interval, exact treatment of bounded coefficients, or proof of identifiability. The mean is the existing least-squares estimate, without a corresponding prior penalty. The regulariser is a fixed scale heuristic, not an inferred physical prior. It is frozen before this comparison and not tuned on suite results.

## Propagation

Integrate the state and its sensitivities to each coefficient together:

    dSx/dt = Sv
    dSv/dt = (-k - 3 b x^2) Sx + (-c - 2 d |v|) Sv
               + [-x, -v, -x^3, -v |v|]

Initial sensitivities are zero because controls are exact and independent of coefficients. For trajectory gradient g(t), local prediction variance is g(t) C g(t)^T.

## Acquisition score

For model weights w_m and predicted positions mu_m(t), compute:

    structural(t) = sum_m w_m [mu_m(t) - weighted_mean(t)]^2
    parameter(t)  = sum_m w_m g_m(t) C_m g_m(t)^T
    score         = mean_t [structural(t) + parameter(t)] / noise_variance

The original active strategy uses only structural(t). Both selectors exclude previously used candidate initial conditions. Score components are saved with the selected experiment. Every method uses identical model fitting, uncertainty estimation, and final-model selection; only experiment selection changes.

This is predictive uncertainty sampling, not expected information gain or an expected reduction in final test error. High uncertainty can reflect an inaccurate local model, so increasing the score does not guarantee better experiments.

## Fixed development suite

- Truth: combined system [1.3, 0.25, 0.9, 0.7]. One setting, not a generalisation benchmark.
- Seeds: 20 and 21, paired across all strategies.
- Budget: four experiments, 41 observations per experiment, four-second trajectories.
- Reference: sensor sigma 0.015, control limit 1.0.
- Noisy: sensor sigma 0.06, control limit 1.0.
- Restricted: sensor sigma 0.015, control limit 0.35.
- Methods: random, systematic, active, active_local.
- Two optimiser starts for every candidate fit and every method.
- No changes to acquisition settings after inspecting suite outcomes.
- Evaluate completed runs on the same twelve continuous unseen starting conditions, scaled to each case's allowed control region.

The runner writes plan.json before any suite experiment. Results report per-case prediction error, structure recovery, learning runtime, and paired final differences. Two seeds and one coefficient setting do not support a statistical superiority claim.

## Validated properties

- Variational trajectory gradients agree with central finite differences.
- An entirely unidentified direction retains positive uncertainty.
- Adding independent Jacobian information reduces local covariance.
- Parameter-aware acquisition remains positive for an uncertain single model even when structural disagreement is zero.

These numerical properties validate implementation mechanics, not empirical calibration or universal scientific usefulness.
