# Milestone 02 — 18 October 2026

## Delivered

- Local coefficient covariance based on the fitted residual Jacobian, with explicit regularisation.
- Variational equations for trajectory sensitivities, checked against numerical derivatives.
- An optional active_local acquisition strategy that combines structural and parameter uncertainty.
- Per-experiment acquisition score decomposition in saved run records.
- Fixed 24-run development suite: three control/noise regimes, two seeds, four methods.
- Side-by-side log-scale learning curves, detailed reports, paired comparisons, and runtime measurements.
- Eleven scientific-contract tests passed.

## Result and decision

The new method did not improve on the original active selector in this suite: five paired final prediction errors tied, and one was worse. The original active strategy remains available with unchanged behaviour; active_local is opt-in and is not promoted to the default.

| Regime | Original active mean final NRMSE | Parameter-aware mean final NRMSE |
|---|---:|---:|
| Reference | 0.00410 | 0.00410 |
| Noisy | 0.01581 | 0.02288 |
| Restricted controls | 0.02688 | 0.02688 |

Both active strategies recovered the correct candidate structure in all six runs each. In the restricted case, random recovered the correct structure in 0/2 runs and systematic in 1/2. These tiny counts are descriptive, not statistical evidence of superiority.

The added score does retain coefficient uncertainty after structural weights concentrate. That is an implementation success, but it does not imply better experiment choices. A predictive-variance score is not the same objective as reducing held-out error.

## Verification

All 24 records have four experiments, four fitted snapshots, and four evaluation snapshots. Controls stay within the case limits and are not repeated. All methods receive identical initial observations for the same seed and case. Recorded Python source hashes match the implementation used throughout the suite. All candidate fits reported successful optimiser termination, without a guarantee of global optimality.

## Scientific limitations

Only one hidden coefficient setting was tested under three regimes. Covariance is a local, regularised approximation, not a calibrated posterior. Initial controls and sensor noise level remain known. No out-of-family dynamics or real apparatus were tested. Results do not establish publishability or robust superiority.

## Recommended next milestone

Expand to diverse coefficient settings with a frozen development/final split before tuning the acquisition rule. Add diagnostics for ambiguous candidate structures and model mismatch. If the local uncertainty approximation is inadequate, compare it with bootstrap uncertainty under the same budget; do not add complexity merely to claim an improvement.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe -m active_discovery.stress_suite --out results/my-uncertainty-suite
```

Completed results: `results/uncertainty-001/report.html` and `results/uncertainty-001/SUMMARY.md`. The original `results/pilot-001` remains unchanged.
