"""Static results report; reads recorded runs, performs no experiments."""
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def write_report(directory):
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    runs = [json.loads((directory/name).read_text(encoding="utf-8")) for name in manifest["runs"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"random": "#64748b", "systematic": "#b45309", "active": "#047857", "active_local": "#6d28d9"}
    for strategy in manifest["strategies"]:
        values = np.array([[m["normalised_rmse"] for m in run["metrics"]]
                           for run in runs if run["strategy"] == strategy])
        x = np.arange(1, values.shape[1]+1)
        for row in values:
            ax.plot(x, row, color=colors[strategy], alpha=0.2, linewidth=1)
        ax.plot(x, values.mean(axis=0), "o-", label=f"{strategy} (mean, n={len(values)})", color=colors[strategy])
    ax.set(xlabel="Experiments acquired", ylabel="Held-out trajectory NRMSE",
           title="Development pilot: prediction error versus experiment budget")
    ax.set_xticks(x)
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(directory/"learning_curves.png", dpi=160)
    plt.close(fig)
    rows = "".join(f"<tr><td>{html.escape(r['system'])}</td><td>{r['seed']}</td><td>{r['strategy']}</td>"
                   f"<td>{r['metrics'][-1]['normalised_rmse']:.4f}</td>"
                   f"<td>{r['rounds'][-1]['best_model']}</td><td>{r['learning_seconds']:.1f}</td></tr>"
                   for r in runs)
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Active Discovery Lab | Pilot</title>
<style>body{{font:16px/1.6 system-ui;background:#f3f5f7;color:#17212b;max-width:1050px;margin:40px auto;padding:0 24px}}
h1{{font-size:36px;margin-bottom:4px}}.notice{{background:#fff2d5;padding:16px;border-left:4px solid #b45309}}
img{{width:100%;background:white}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}code{{background:#e4e8ed;padding:2px 5px}}</style>
<h1>Active Discovery Lab</h1><p>Can an algorithm choose better experiments to identify hidden dynamics?</p>
<p class="notice"><b>Development pilot.</b> These runs verify the pipeline. They do not establish superiority, novelty, or generalisation to unseen system families.</p>
<h2>Prediction on unseen starting conditions</h2><img src="learning_curves.png" alt="Error by experiment count for each selection strategy">
<p>Faint lines show individual runs; bold lines show means, not confidence bounds. Lower error is better. All methods start with the same observation and receive paired per-round noise.</p>
<table><tr><th>System</th><th>Seed</th><th>Strategy</th><th>Final NRMSE</th><th>Selected model</th><th>Learning seconds</th></tr>{rows}</table>
<h2>What this version establishes</h2><p>The learner receives noisy positions only, fits four candidate equation structures, and selects experiments without evaluator feedback. Each completed run is evaluated on twelve reproducible unseen starting conditions.</p>
<h2>Limitations</h2><p>Known noise level; exact initial controls; in-family dynamics; no calibrated confidence or reliable refusal mechanism yet. The active strategy uses structural disagreement only; active_local adds a regularised local parameter covariance and first-order sensitivity propagation. Neither its covariance nor its tempered BIC weights are calibrated posterior estimates. Boundary effects, multimodality, and nonlinear uncertainty are not captured. A separate final system set and larger paired trials remain necessary.</p>
<p>Protocol and source hashes: <a href="manifest.json">manifest.json</a>. Full observations and fitted coefficients are in the adjacent run JSON files.</p></html>"""
    (directory/"report.html").write_text(page, encoding="utf-8")
