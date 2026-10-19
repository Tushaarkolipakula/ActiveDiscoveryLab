# Milestone 01 — 18 October 2026

## Completed

- Desktop project with an isolated Python environment and local Git repository.
- Hidden simulation API, direct trajectory fitting, four candidate structures, three selection strategies.
- Separate post-run evaluation, complete run records, manifest/source hashes, dependency lockfile, static report.
- Seven scientific-contract tests passed.
- Pilot: four systems x two noise/optimiser seeds x three strategies, four experiments per run (24 runs).
- All 384 candidate fits reported successful optimiser termination. This does not certify global optimality.

## Observed result

All 24 runs selected the correct structural family by their fourth experiment. Mean held-out NRMSE after two experiments was 0.04301 for random, 0.00494 for systematic, and 0.00494 for active selection. Final mean errors were 0.00272, 0.00300, and 0.00266 respectively.

Active selection did not demonstrate a meaningful advantage over the systematic baseline. Its final error was lower than random in only 3/8 paired cases, and lower than systematic in 5/8. These are descriptive pilot outcomes, not significance tests. The near-equal systematic/active performance indicates that a simple broad excitation already solves much of this easy in-family problem.

## Next scientific milestone

Before adding a dashboard or making stronger claims:

1. Inspect where the acquisition scores collapse after model weights concentrate.
2. Add parameter uncertainty to the candidate predictions and compare with structural-only uncertainty.
3. Preserve the same fitter/budget across methods; do not weaken systematic baselines to manufacture a gain.
4. Predefine harder development cases (limited control range, increased noise, uncertain controls) and separately reserve final-test systems.
5. Investigate whether indistinguishable hypotheses can be reported honestly rather than forcing a unique conclusion.

The pilot establishes a working foundation, not a finished research contribution. See results/pilot-001/SUMMARY.md and report.html for exact results.
