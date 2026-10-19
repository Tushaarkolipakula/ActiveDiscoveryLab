# Parameter-aware revision

The earlier structural selector sometimes assigned effectively all weight to one equation. Its structural disagreement then vanished even when its coefficients were still uncertain. This implementation extends the existing regularized local-covariance method to all revised models.

For a fitted residual Jacobian J (already divided by known sensor noise), parameter-bound widths D and a fixed precision of 12:

    C = D [(J D)' (J D) + 12 I]^-1 D

The parameter vector includes four base coefficients and one bias coefficient, three sinusoidal coefficients, or one smooth friction coefficient. Covariance has the corresponding 5×5 or 7×7 shape. State sensitivities are obtained by integrating variational equations; the sinusoidal frequency derivative is t[A cos(ωt) − B sin(ωt)].

For candidate experiment e, the selection score is the time-averaged sum of structural prediction disagreement and within-model local variance g C g', divided by sensor-noise variance. Model-score weights are unchanged. The maximum-scoring unused starting condition is selected. Every comparison policy uses identical fitting, revision criteria and model complexity penalties.

This is a heuristic predictive-uncertainty score, not expected information gain. Covariance is neither calibrated nor a full posterior. It ignores separate optimizer modes, coefficient-bound truncation and uncertainty in noise. Positive acquisition does not imply improved prediction. Unconverged fits and poor-fit evidence remain visible in results.

## Frozen evaluation

Four new coefficient settings (ordinary combined dynamics, periodic force, constant force, smooth friction); two paired noise seeds (211 and 307); three policies (structural revision, random revision, local-uncertainty revision); four acquired experiments per run; known noise standard deviation 0.025; forty unseen test initial conditions. The primary metric averages test NRMSE across rounds 2–4 and then averages paired seeds within each system. The test conditions and source hashes are written before training.

This is 24 runs and four independent designed systems, not 24 independent physical systems. It is a modest replication, not sufficient evidence for broad superiority. Compare each policy on the same systems, noise seeds, test trajectories and acquisition budget. Wall times on a shared laptop are descriptive only.

## Verification

Analytic sensitivities are checked against finite differences. New tests verify positive uncertainty in unseen directions, contraction with added information, and nonzero acquisition after all weight concentrates on a single expanded model. Raw records retain covariance, selected controls, score components, residual warnings, exact coefficients and prediction errors.

The physical Silverbox experiment remains a separate passive baseline; these new experiments do not turn it into hardware active-learning evidence.
