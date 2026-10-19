# Active Discovery Lab

**Can a system choose informative experiments to learn hidden dynamics with fewer measurements?**

An autonomous experimental-design prototype for a simulated cart-and-spring system. It observes noisy positions, fits candidate equations, chooses another initial condition, and is evaluated on unseen starting conditions after discovery ends.

## Status

Version 0.5 adds parameter-aware selection for revised equations and a new 24-run multi-seed comparison. Version 0.4 introduced finite-library revision and separate passive validation on measured Silverbox circuit data. The project includes a live local laboratory, preserved baseline evaluations and explicit limitations. It does not claim unrestricted discovery, established active-selection superiority or active experiments on physical hardware.

## Live laboratory

From the project folder, run `run-lab.ps1`, or:

```powershell
.\.venv\Scripts\python.exe -m active_discovery.lab --port 8765
```

Open http://127.0.0.1:8765. Launch a live CPU investigation or inspect recorded experiments. The UI displays measured motion, fitted hypotheses, evidence flags and post-run validation. It listens only on localhost. Press Ctrl+C in the serving terminal to stop it.

The completed evaluation is at `results/research-001/report.html`; `demo-replay.html` in that folder works offline and is explicitly a replay. Start with `docs/PROFESSOR_BRIEF.md` for the research question, results, limitations and demonstration outline.

Evidence flags distinguish competing structures, a preferred structure, poor fit, and optimiser warnings. They are heuristics, not calibrated confidence or refusal guarantees. The detect-and-revise strategy opens three additional equation families after inadequate fit on at least two experiments. Select the external-force world to demonstrate it. See `results/revision-001/REPORT.md` and `results/silverbox-001/REPORT.md` for the new evidence; `docs/REAL_DATA.md` explains the measured-data protocol.

## Quick start

The Desktop installation includes `.venv`. In PowerShell, from this project:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m active_discovery.benchmark --budget 4 --seeds 0 1 --out results/my-pilot
```

For a new computer with Python 3.11 or newer:

```bash
python -m venv .venv
# Activate the environment using the command appropriate to your shell.
python -m pip install -e .
python -m unittest discover -s tests -v
python -m active_discovery.benchmark --budget 4 --seeds 0 1 --out results/my-pilot
```

Open `results/my-pilot/report.html`. It is a static local report, not a running service. Use a fresh output directory each run; existing results are never silently overwritten.

Run the parameter-uncertainty comparison (24 CPU runs):

```powershell
.\.venv\Scripts\python.exe -m active_discovery.stress_suite --out results/my-uncertainty-suite
```

This compares four strategies under reference, noisy, and restricted-control conditions. It writes its plan before running and produces `report.html`, `SUMMARY.md`, and per-case run records. See `docs/UNCERTAINTY.md` for the approximation and its limitations.

## Scientific scope

Hidden dynamics: `x'' = -k*x - c*v - b*x^3 - d*v*abs(v)` with mass-normalised coefficients. The learner knows this restricted family and coefficient bounds, but not the active terms or values.

Four structures: linear spring/damping; additional cubic spring; additional quadratic drag; both additions. Coefficients are fitted to whole trajectories using bounded multistart least squares. Observations are not numerically differentiated.

Every method starts from the same small displacement. Subsequent experiments use a 5-by-5 grid of initial position and velocity, excluding the equilibrium. No repeats. Each experiment lasts four seconds, has 41 observations, and receives independent Gaussian sensor noise with known standard deviation. Initial controls are exact.

- **Random:** sample an unused allowed experiment uniformly.
- **Systematic:** follow a fixed farthest-first space-filling sequence.
- **Active:** maximise temporal-average weighted prediction disagreement divided by sensor variance.
- **Active local:** add within-model parameter uncertainty, propagated through trajectory sensitivities, to the same disagreement score.

Candidate weights use BIC with known noise variance and fixed temperature 2. They are heuristic weights, not calibrated posterior probabilities. All methods use the same fitter and receive a regularised covariance derived from its residual Jacobian. Only active_local uses that covariance for selection. The original active selector cannot detect remaining uncertainty within a single model. Multistart fitting alone is not an uncertainty estimator.

## Layout

```text
active_discovery/
  environment.py   # measurement contract and forward simulation
  models.py        # candidate structures, trajectory fitting, model scores
  selection.py     # four experiment-selection strategies
  runner.py        # budgeted discovery loop; no evaluation access
  evaluation.py    # separate held-out trajectory and structure metrics
  benchmark.py     # paired trials, manifests, persistence
  report.py        # saved-results chart and HTML report
  stress_suite.py  # fixed development cases, four methods, paired seeds
  stress_report.py # per-case comparisons and aggregate report
tests/
docs/ARCHITECTURE.md
docs/EXPERIMENT_PROTOCOL.md
```

## Reproducibility

Each result directory stores a manifest (protocol, package versions, source hashes, seeds), complete observations and fitted models for every round, evaluation metrics, and learning time. Paired trials use identical starting observations and per-round measurement noise across strategies. Random seeds are explicitly controlled. Cross-platform floating-point results need not be bitwise identical.

The environment uses tighter tolerances and a different ODE integration method than the learner. This avoids exact numerical equivalence, but both still share the same mathematical family. This is a deliberately favourable synthetic benchmark.

## Next milestones

1. Validate the pipeline and report baseline outcomes without cherry-picking.
2. Evaluate the local parameter-uncertainty approximation and acquisition-score collapse; use bootstrap ensembles if the local approximation proves inadequate.
3. Freeze a separate development/final-test system split and run larger paired trials.
4. Test model mismatch and explicit insufficient-evidence behaviour.
5. Only then consider symbolic regression, a visual laboratory, and physical experiments.

CPU-first implementation. No GPU, remote credentials, external model API, or LLM is required.

## Reproduce the new evaluations

```powershell
.\.venv\Scripts\python.exe -m active_discovery.revision_suite --out results/my-revision-run
.\download-silverbox.ps1
.\.venv\Scripts\python.exe -m active_discovery.silverbox --out results/my-silverbox-run
```

Use a new output directory for each run. The recorded plans and results are evidence already inspected, not untouched future test sets.

## Parameter-aware revision

The optional `revision_local` policy combines structural disagreement with local parameter prediction variance, including added force parameters. It addresses a vanished acquisition signal when one structure dominates; it does not guarantee better choices. The default revision policy remains available. See `results/replication-001/REPORT.md` and `docs/REVISION_UNCERTAINTY.md`.

```powershell
.\.venv\Scripts\python.exe -m active_discovery.replication_suite --out results/my-replication-run
```
