# Research positioning

This repository is currently a reproducible engineering baseline, not a novel scientific-discovery algorithm.

## Relevant primary sources

- Brunton, Proctor and Kutz, *Discovering governing equations from data by sparse identification of nonlinear dynamical systems* (2016): https://doi.org/10.1073/pnas.1517384113 . Establishes sparse identification of governing dynamical equations from a candidate function library.
- *Ensemble-SINDy: Robust sparse model discovery in the low-data, high-noise limit, with active learning and control*: https://pmc.ncbi.nlm.nih.gov/articles/PMC9006119/ . Directly relevant prior work: ensemble forecast variance is used to select initial conditions for active learning. Therefore, selecting experiments by model disagreement is not a novelty claim for this project.
- Udrescu and Tegmark, *AI Feynman: a Physics-Inspired Method for Symbolic Regression*: https://arxiv.org/abs/1905.11481 . Relevant to a later move beyond the fixed four-structure candidate library.

## Current distinctions, not established contributions

Our prototype observes noisy position only and fits integrated trajectories directly. It compares a small explicit set of structural hypotheses using a single shared fitter and transparent data-access boundaries. These are implementation choices, not demonstrated research innovations.

## Questions worth investigating after the baseline

1. Does structural disagreement become uninformative once model weights concentrate, even when coefficient uncertainty remains high?
2. Does an ensemble representing both parameter and structural uncertainty improve experiment efficiency over either alone?
3. Under restricted interventions, can an algorithm reliably report that multiple models remain observationally indistinguishable?
4. How does direct trajectory fitting compare with derivative-based or weak-form identification when only position is measured?

Before claiming a new contribution, review related work for the chosen question, establish an appropriate baseline (potentially E-SINDy or a trajectory-compatible analogue), and reserve final test conditions. A successful pilot alone does not establish publishability.
