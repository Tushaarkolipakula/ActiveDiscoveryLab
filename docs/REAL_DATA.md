# Physical measurements on a laptop

Silverbox is a measured electronic implementation of a Duffing oscillator. It provides input/output voltage recordings; it is not a simulator generated for this project.

Source: https://sites.google.com/view/nonlinear-benchmark/benchmarks/silverbox

Citation: T. Wigren and J. Schoukens. Three free data sets for development and benchmarking in nonlinear system identification. European Control Conference, 2013, pp. 2933–2938. DOI: 10.23919/ECC.2013.6669201.

The split follows the maintainer's implementation at https://github.com/MaartenSchoukens/nonlinear_benchmarks/blob/master/nonlinear_benchmarks/benchmarks.py (accessed 19 October 2026). Python half-open ranges: train/validation [40650,101212), multisine test [101212,127400), full arrow test [100,40575). Only 50 measured outputs initialize each test; all subsequent outputs are freely predicted from past predictions and recorded inputs. Internal validation uses the chronological last 20% of train/validation. Scaling is learned from training only. Five regularization values are compared per model; no test-based tuning is performed.

This stage compares linear ARX(2) and the same predictor with one cubic delayed-output feature. The cubic term was chosen using the published system description, so this is not a discovery of unknown circuit physics. The noise and discretization assumptions differ from the active continuous-time simulator. These results establish a passive prediction baseline, not successful physical interventions or state-of-the-art performance.

Run from the project directory:

```powershell
.\download-silverbox.ps1
.\.venv\Scripts\python.exe -m active_discovery.silverbox --out results/my-silverbox-run
```

The original data archive is retained locally under `data/silverbox`, with its original README. Raw third-party data is excluded from source bundles and Git; use the source link and download script to obtain it. No additional redistribution license is asserted. SHA-256 of the exact MAT file, the split, selected coefficients, validation outcomes, final test metrics and a figure are saved in the results folder. Existing nonempty result folders are never overwritten.
