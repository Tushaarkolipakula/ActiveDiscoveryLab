"""Aggregate frozen stress cases with descriptive paired comparisons."""
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def write_stress_report(directory):
    directory = Path(directory)
    plan = json.loads((directory/'plan.json').read_text(encoding='utf-8'))
    rows, all_runs = [], []
    colors = {'random': '#64748b', 'systematic': '#b45309', 'active': '#047857', 'active_local': '#6d28d9'}
    fig, axes = plt.subplots(1, len(plan['cases']), figsize=(15, 4.8), sharey=True)
    for ax, case in zip(np.atleast_1d(axes), plan['cases']):
        manifest = json.loads((directory/case['name']/'manifest.json').read_text(encoding='utf-8'))
        runs = [json.loads((directory/case['name']/name).read_text(encoding='utf-8')) for name in manifest['runs']]
        for run in runs:
            run['case'] = case['name']
        all_runs.extend(runs)
        for strategy in plan['strategies']:
            group = [run for run in runs if run['strategy'] == strategy]
            values = np.array([[m['normalised_rmse'] for m in r['metrics']] for r in group])
            x = np.arange(1, values.shape[1]+1)
            for row in values:
                ax.plot(x, row, color=colors[strategy], alpha=.22, linewidth=1)
            ax.plot(x, values.mean(axis=0), 'o-', label=strategy, color=colors[strategy], markersize=4)
            rows.append({'case': case['name'], 'strategy': strategy, 'n': len(group),
                         'after_two': float(values[:, 1].mean()), 'final': float(values[:, -1].mean()),
                         'structure_correct': sum(r['metrics'][-1]['structure_correct'] for r in group),
                         'learning_seconds': float(np.mean([r['learning_seconds'] for r in group]))})
        ax.set_title(f"{case['name']}\nnoise={case['noise']}, controls=±{case['control_limit']}")
        ax.set_xlabel('Experiments acquired')
        ax.set_xticks(x)
        ax.set_yscale('log')
        ax.grid(alpha=.2)
    np.atleast_1d(axes)[0].set_ylabel('Held-out trajectory NRMSE (log scale)')
    handles, labels = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=4, bbox_to_anchor=(.5, 0))
    fig.suptitle('Parameter-aware selection: development stress test, two seeds per case')
    fig.tight_layout(rect=(0, .07, 1, .92))
    fig.savefig(directory/'comparison.png', dpi=160)
    plt.close(fig)
    lookup = {(r['case'], r['seed'], r['strategy']): r for r in all_runs}
    comparisons = []
    for baseline in ['random', 'systematic', 'active']:
        pairs = [(r, lookup[(r['case'], r['seed'], baseline)]) for r in all_runs if r['strategy'] == 'active_local']
        delta = [a['metrics'][-1]['normalised_rmse']-b['metrics'][-1]['normalised_rmse'] for a, b in pairs]
        comparisons.append({'baseline': baseline, 'pairs': len(pairs),
                            'lower_final_error': sum(value < 0 for value in delta),
                            'mean_final_difference': float(np.mean(delta))})
    diagnostics = {'failed_fit_terminations': sum(not f['converged'] for r in all_runs for s in r['rounds'] for f in s['fits']),
                   'total_runs': len(all_runs), 'rows': rows, 'paired_comparisons': comparisons}
    (directory/'summary.json').write_text(json.dumps(diagnostics, indent=2), encoding='utf-8')
    lines = ['# Milestone 02: local parameter uncertainty', '',
             'Development results only. One coefficient setting, three observation/control regimes, two seeds per regime. These do not establish statistical superiority or broader generalisation.', '',
             '| Case | Strategy | Mean NRMSE at 2 | Mean final NRMSE | Correct structure | Mean learning seconds |',
             '|---|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['strategy']} | {r['after_two']:.5f} | {r['final']:.5f} | {r['structure_correct']}/{r['n']} | {r['learning_seconds']:.1f} |")
    lines += ['', '## Paired comparisons', '']
    for c in comparisons:
        lines.append(f"- active_local has lower final prediction error than {c['baseline']} in {c['lower_final_error']}/{c['pairs']} pairs. Mean difference (active_local minus baseline): {c['mean_final_difference']:.5f}.")
    lines += ['', f"Unsuccessful optimiser terminations: {diagnostics['failed_fit_terminations']}.", '',
              'The local approximation is regularised and may be unreliable at bounds, for nonlinear uncertainty, or for multiple fit modes. Structure identification and predictive accuracy are distinct. No calibrated confidence or refusal is claimed.']
    (directory/'SUMMARY.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    table = ''.join(f"<tr><td>{r['case']}</td><td>{r['strategy']}</td><td>{r['after_two']:.5f}</td><td>{r['final']:.5f}</td><td>{r['structure_correct']}/{r['n']}</td><td>{r['learning_seconds']:.1f}</td></tr>" for r in rows)
    links = ' · '.join(f'<a href="{c["name"]}/report.html">{html.escape(c["name"])} details</a>' for c in plan['cases'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Active Discovery Lab — uncertainty experiment</title>
<style>body{{font:16px/1.6 system-ui;background:#f3f5f7;color:#17212b;max-width:1250px;margin:35px auto;padding:0 20px}}h1{{font-size:32px}}.notice{{background:#fff2d5;padding:15px}}img{{width:100%}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #ddd}}pre{{white-space:pre-wrap}}</style>
<h1>Does parameter uncertainty improve experiment selection?</h1>
<p>active_local adds within-model parameter uncertainty to the original structural-disagreement score. All methods use the same fitter, controls, observations per experiment, and budget.</p>
<p class="notice">Development evidence only: two seeds per regime and one hidden coefficient setting. No statistical superiority claim. The plan was saved before running the suite.</p>
<img src="comparison.png" alt="Learning curves for reference, noisy, and restricted-control cases">
<p>Faint lines are individual runs; bold lines are means. Log scale; lower is better. These are not confidence intervals.</p>
<table><tr><th>Case</th><th>Strategy</th><th>NRMSE at 2</th><th>Final NRMSE</th><th>Correct structure</th><th>Learning seconds</th></tr>{table}</table>
<h2>Interpretation and limitations</h2><pre>{html.escape(chr(10).join(lines[lines.index('## Paired comparisons')+1:]))}</pre>
<p>{links} · <a href="plan.json">Frozen plan</a> · <a href="summary.json">Machine-readable summary</a></p></html>'''
    (directory/'report.html').write_text(page, encoding='utf-8')
    return '\n'.join(lines)
