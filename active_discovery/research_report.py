"""All cases, paired system-level comparisons, diagnostic outcomes."""
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def write_report(directory):
    directory = Path(directory)
    plan = json.loads((directory/'plan.json').read_text())
    runs = [json.loads((directory/name).read_text()) for name in json.loads((directory/'index.json').read_text())]
    main = [r for r in runs if r['split'] == 'frozen_evaluation']
    mismatch = [r for r in runs if r['split'] != 'frozen_evaluation']
    ids = [c['id'] for c in plan['cases'] if c['split'] == 'frozen_evaluation']
    scores = {}
    for method in plan['strategies']:
        scores[method] = np.array([np.mean([np.mean([m['normalised_rmse'] for m in r['metrics'][1:]])
                                          for r in main if r['case'] == case and r['strategy'] == method]) for case in ids])
    rng = np.random.default_rng(771)
    indices = rng.integers(0, len(ids), (5000, len(ids)))
    comparisons = []
    for baseline in ['random', 'systematic']:
        delta = scores['active']-scores[baseline]
        interval = np.quantile(delta[indices].mean(axis=1), [.025, .975]).tolist()
        comparisons.append({'baseline': baseline, 'mean_paired_difference': float(delta.mean()),
                            'bootstrap_95_interval': interval, 'systems_with_lower_error': int((delta < 0).sum()),
                            'systems': len(ids)})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.6))
    colors = {'random': '#64748b', 'systematic': '#b45309', 'active': '#047857'}
    for method in plan['strategies']:
        values = np.array([[m['normalised_rmse'] for m in r['metrics']] for r in main if r['strategy'] == method])
        ax.plot([1, 2, 3, 4], values.mean(axis=0), 'o-', label=method, color=colors[method])
    ax.set(xlabel='Experiments', ylabel='Mean held-out NRMSE', title='Eight systems, two seeds each')
    ax.set_xticks([1, 2, 3, 4]); ax.set_yscale('log'); ax.grid(alpha=.2); ax.legend()
    for offset, baseline in enumerate(['random', 'systematic']):
        bx.scatter(np.arange(len(ids))+.12*offset, scores['active']-scores[baseline], label=f'active minus {baseline}', alpha=.8)
    bx.axhline(0, color='#64748b', linewidth=1)
    bx.set_xticks(np.arange(len(ids)), ids, rotation=45, ha='right')
    bx.set(ylabel='Paired difference in primary error', title='Each dot is a system; negative favours active')
    bx.legend(); bx.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(directory/'research.png', dpi=160); plt.close(fig)
    counts = {}
    for method in plan['strategies']:
        group = [r for r in main if r['strategy'] == method]
        counts[method] = {'correct_structures': sum(r['metrics'][-1]['structure_correct'] for r in group),
                          'runs': len(group), 'ambiguous_final': sum(r['rounds'][-1]['evidence']['status'] == 'ambiguous' for r in group),
                          'poor_fit_final': sum(r['rounds'][-1]['evidence']['status'] == 'poor_fit' for r in group),
                          'mean_primary_error': float(scores[method].mean()),
                          'mean_seconds': float(np.mean([r['learning_seconds'] for r in group]))}
    flagged = sum(r['rounds'][-1]['evidence']['status'] == 'poor_fit' for r in mismatch)
    result = {'comparisons': comparisons, 'methods': counts, 'mismatch_flags': flagged,
              'mismatch_runs': len(mismatch), 'case_scores': {k: v.tolist() for k,v in scores.items()},
              'case_ids': ids, 'total_runs': len(runs)}
    (directory/'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Frozen multi-system evaluation', '',
             'Primary metric: mean held-out trajectory NRMSE across rounds 2–4, averaging both noise seeds within each system.', '',
             '| Method | Mean primary error | Correct final structures | Ambiguous final | Poor-fit flags (in-family) |',
             '|---|---:|---:|---:|---:|']
    for method, c in counts.items():
        lines.append(f"| {method} | {c['mean_primary_error']:.5f} | {c['correct_structures']}/{c['runs']} | {c['ambiguous_final']} | {c['poor_fit_final']} |")
    lines += ['', '## Paired comparisons', '']
    for c in comparisons:
        low, high = c['bootstrap_95_interval']
        lines.append(f"- Active minus {c['baseline']}: {c['mean_paired_difference']:.5f}; descriptive 95% system-bootstrap interval [{low:.5f}, {high:.5f}]. Lower error on {c['systems_with_lower_error']}/{c['systems']} systems.")
    lines += ['', f"Out-of-family stress: poor-fit warning on {flagged}/{len(mismatch)} completed runs.", '',
              'Eight systems are a small, designed sample, not a representative population. Bootstrap intervals are descriptive and not corrected for multiple comparisons. Poor-fit and ambiguity diagnostics are heuristics, not calibrated refusal guarantees. This test set is now consumed; future tuning requires new final-test systems.']
    text = '\n'.join(lines)
    (directory/'SUMMARY.md').write_text(text+'\n', encoding='utf-8')
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Active Discovery Lab — research evidence</title>
<style>body{{font:16px/1.6 system-ui;background:#f3f5f7;color:#17212b;max-width:1150px;margin:40px auto;padding:0 24px}}img{{width:100%}}pre{{white-space:pre-wrap;background:white;padding:22px}}a{{color:#047857}}</style>
<h1>What survives a broader test?</h1><p>54 completed runs · 8 frozen in-family systems · 2 deliberately mismatched systems · 50 unseen trajectories per run snapshot.</p>
<img src="research.png" alt="Learning curves and paired errors across eight systems"><pre>{html.escape(text)}</pre>
<p><a href="plan.json">Frozen protocol and source hashes</a> · <a href="summary.json">Summary data</a> · <a href="index.json">All run records</a></p></html>'''
    (directory/'report.html').write_text(page, encoding='utf-8')
    return text
