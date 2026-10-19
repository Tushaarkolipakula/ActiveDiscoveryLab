# Version 0.5 update: parameter-aware revision

The new optional selector propagates local uncertainty in all fitted parameters, including added force parameters, into predicted trajectories. This retains a selection signal when structural disagreement collapses. It is a regularized local approximation, not calibrated Bayesian inference or expected information gain.

A new frozen comparison completed 24 runs: four new designed systems, two paired noise seeds and three selection policies, with equal four-experiment budgets. Forty unseen initial conditions are used for post-run evaluation. The primary metric averages error over rounds 2–4, then averages seeds within systems.

The parameter-aware policy improved the primary metric in 3/4 systems versus structural revision, but its mean difference was +0.000124 (slightly worse overall). Versus random revision, it improved 3/4 systems with mean difference −0.012220. These four-system descriptive results do not establish general superiority; the new policy remains optional. Final-round error and the predeclared primary metric are different measures.

The implementation fixes the vanished uncertainty signal, but does not establish a reliable average accuracy gain over structural revision. This negative result is retained, alongside all raw outcomes and frozen source hashes. The live parameter-aware investigation completed successfully. There are 28 automated tests including a new stable replay-ID regression test; the core 27-test suite and the updated three-test lab suite passed.

Open `results/replication-001/report.html` for the full comparison and `docs/REVISION_UNCERTAINTY.md` for the derivation and limitations. Reproduce with `python -m active_discovery.replication_suite --out results/new-replication`.

Interview framing: investigated a failure mode in finite-library experimental design, implemented parameter-aware acquisition, and evaluated the proposed fix against paired baselines while preserving negative results. Do not describe the new method as a proven improvement or a novel general AI scientist.

---

# Active Discovery Lab — professor briefing

Research question: can an experimental-design system recognize that its equations are inadequate, expand a finite hypothesis library, and test the revised explanation?

## What is implemented

Noisy position measurements → bounded trajectory fitting → residual and ambiguity checks → finite-library revision → experiment selection → separate held-out evaluation. The learner receives measurements and permitted starting controls; ground truth and test errors are withheld until discovery is complete. The local browser lab supports live computation and offline recorded replay.

## Revision evidence

A frozen 20-run comparison uses five systems, four policies, four experiments and 30 unseen test trajectories per run. The table shows final normalized prediction error; lower is better. One seed per system makes this descriptive, not a statistically established advantage.

| System | Fixed active | Always expanded | Revision active | Revision random |
|---|---:|---:|---:|---:|
| control | 0.00595 | 0.00218 | 0.00595 | 0.00825 |
| periodic | 0.13693 | 0.00671 | 0.00513 | 0.00867 |
| bias | 0.42548 | 0.00338 | 0.00338 | 0.00971 |
| dry | 0.13687 | 0.02435 | 0.02435 | 0.01051 |
| outside-grammar | 0.21982 | 0.07372 | 0.07372 | 0.07442 |

Revision successfully selected the added mechanism in the designed periodic, constant-force and dry-friction cases. The ordinary control did not trigger revision. Always-expanded fitting can match or beat adaptive revision; random interventions beat active selection on the friction case. Structural disagreement may collapse once a model dominates, leaving weak guidance for subsequent experiments. The chirp remains outside the grammar; lower error there does not mean the true law was recovered.

## Physical measurements: a separate validation

Using the public Silverbox electronic-oscillator recordings, a cubic autoregressive baseline achieved 4.388 mV and 5.439 mV free-running test RMSE, versus 7.708 mV and 15.465 mV for a linear baseline. Only the first 50 measured test outputs initialize predictions. Hyperparameters use an internal training/validation split, and selected models are frozen before official test scoring. This validates passive prediction on physical measurements, not active interventions on hardware. The cubic feature is informed by the published apparatus description.

## Reliability and prior evidence

24 automated tests passed. A live revision investigation completed successfully in the browser. The earlier 54-run evaluation and its negative results are preserved: active-versus-systematic uncertainty intervals crossed zero, so broad active-selection superiority is not established. All new comparison outcomes, plans, model parameters and source hashes are retained.

## Five-minute demonstration

1. Launch `run-lab.ps1` and open http://127.0.0.1:8765. Select the periodic revision replay.
2. Show experiment 1: the original equations fail. Show experiment 2: the library expands.
3. Show the final equation, unseen-trajectory error and revealed simulator truth.
4. Compare the fixed-library result and inspect the out-of-grammar case.
5. Open the Silverbox report to distinguish physical recordings from simulated interventions.

## Resume wording supported by the evidence

Built a CPU-based experimental-design prototype that detects model mismatch, expands a finite dynamical-equation library, and evaluates revised models on unseen trajectories; benchmarked four policies across 20 revision runs and separately evaluated free-running predictors on measured Silverbox circuit data, with an interactive laboratory and 24 automated tests.

Do not claim unrestricted scientific discovery, a newly discovered physical law, calibrated confidence, state-of-the-art performance, or active hardware validation. A stronger next research step is multi-seed replication on new systems and parameter-aware selection after model weights collapse.

Dataset source: https://sites.google.com/view/nonlinear-benchmark/benchmarks/silverbox
Citation: T. Wigren and J. Schoukens, European Control Conference (2013), pp. 2933–2938.
