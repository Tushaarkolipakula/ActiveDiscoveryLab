# Milestone 03 — 19 October 2026

The scientist now exposes heuristic evidence states: preferred candidate, ambiguity, poor model fit, and optimiser warnings. A local browser laboratory runs real experiments on the laptop, updates after each fit, and reveals simulator truth only after discovery ends. Recorded and live modes are labelled separately.

## Validation

Sixteen scientific-engine/diagnostic tests and two lab-input tests passed. A live four-experiment run completed successfully and was persisted in results/live. The 54-run research evaluation completed, and all source hashes recorded at its start still matched the numerical implementation when checked after completion.

## Measured outcome

Active selection's primary mean error was 0.02616, versus 0.02760 for systematic and 0.03056 for random selection. Both descriptive paired bootstrap intervals include zero; superiority remains unproven. Each method selected the correct final family in 15/16 in-family runs.

The poor-fit diagnostic flagged all six externally forced mismatch runs. No in-family run had a final poor-fit flag. These counts are specific to the designed benchmark, not general detector performance estimates.

## Next milestone

Model inadequacy -> candidate revision -> discriminating experiment -> independent validation. Preserve the fixed-library system as a baseline, and evaluate whether expansion actually improves predictions without unnecessary complexity. A controlled real-physics validation can follow a working revision loop.

See PROFESSOR_BRIEF.md for presentation guidance and honest claim boundaries. Full results are in results/research-001.
