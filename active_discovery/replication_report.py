"""Readable standalone evidence report from completed replication records."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import numpy as np


def build(directory):
    directory=Path(directory)
    plan=json.loads((directory/'plan.json').read_text())
    index=json.loads((directory/'index.json').read_text())
    expected={(c['id'],s,p) for c in plan['cases'] for s in plan['seeds'] for p in plan['policies']}
    runs=[json.loads((directory/name).read_text()) for name in index]
    actual={(r['case'],r['seed'],r['strategy']) for r in runs}
    if actual!=expected or len(runs)!=len(expected): raise ValueError('Incomplete or duplicate run matrix.')
    for name,digest in plan['source_sha256'].items():
        if hashlib.sha256((directory/'source'/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Frozen source mismatch: {name}')
    for r in runs:
        controls=[(o['experiment']['position'],o['experiment']['velocity']) for o in r['observations']]
        assert len(set(controls))==len(controls)==plan['budget']
        assert len(r['metrics'])==plan['budget']
        assert all(np.isfinite(m['normalised_rmse']) for m in r['metrics'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors=['#397b9c','#a95b24','#176b52']
    labels=['Structural revision','Random revision','Parameter-aware revision']
    fig,axes=plt.subplots(1,4,figsize=(13,3.6),sharey=False)
    rows=[]
    for ax,case in zip(axes,plan['cases']):
        for policy,color,label in zip(plan['policies'],colors,labels):
            selected=[r for r in runs if r['case']==case['id'] and r['strategy']==policy]
            errors=np.array([[m['normalised_rmse'] for m in r['metrics']] for r in selected])
            ax.plot(range(1,5),errors.mean(axis=0),marker='o',color=color,label=label)
            ax.fill_between(range(1,5),errors.min(axis=0),errors.max(axis=0),color=color,alpha=.12)
            for r in selected:
                primary=np.mean([m['normalised_rmse'] for m in r['metrics'][1:]])
                rows.append(f"<tr><td>{html.escape(r['case'])}</td><td>{r['seed']}</td><td>{html.escape(label)}</td><td>{primary:.5f}</td><td>{r['metrics'][-1]['normalised_rmse']:.5f}</td><td>{html.escape(r['rounds'][-1]['evidence']['status'])}</td></tr>")
        ax.set(title=case['id'],xlabel='Experiments',xticks=[1,2,3,4],yscale='log')
        ax.grid(alpha=.2)
    axes[0].set_ylabel('Unseen-trajectory NRMSE (log scale)')
    handles,legend=axes[0].get_legend_handles_labels()
    fig.legend(handles,legend,loc='lower center',ncol=3,frameon=False)
    fig.suptitle('New systems, paired noise seeds, equal experiment budgets')
    fig.tight_layout(rect=(0,.1,1,.94))
    chart=directory/'learning_curves.png';fig.savefig(chart,dpi=160);plt.close(fig)
    summary=json.loads((directory/'summary.json').read_text())
    comparisons=''.join(f"<li>Against {html.escape(baseline)}: lower mean primary error in <b>{s['cases_improved']}/{s['case_count']} systems</b>; mean paired difference {s['mean_difference']:.5f} (negative favors parameter-aware).</li>" for baseline,s in summary.items())
    content=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Active Discovery Lab — replication evidence</title><style>
body{{font:16px/1.65 system-ui,sans-serif;color:#183c33;background:#f7f6ef;margin:0}}main{{max-width:1100px;margin:auto;padding:36px 24px}}h1{{font:42px/1.15 Georgia,serif}}h2{{margin-top:36px}}.note{{padding:18px;background:#e7eee3;border-left:4px solid #176b52}}img{{width:100%;height:auto;background:white}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid #d7dfd5;text-align:left;padding:9px}}.scroll{{overflow-x:auto}}small{{color:#57685c}}
</style><main><small>ACTIVE DISCOVERY LAB · VERSION 0.5 · 19 OCTOBER 2026</small>
<h1>Does remembering parameter uncertainty improve the next experiment?</h1>
<p>When one equation dominates, disagreement between equation families can disappear. Its coefficients can still be uncertain. The new selector propagates that local coefficient uncertainty into predicted trajectories and uses it alongside structural disagreement.</p>
<div class="note"><b>Completed evidence:</b> 24 runs, four new designed systems, two paired noise seeds, three policies, four acquired experiments per run, forty unseen validation trajectories. Frozen source hashes and the full run matrix passed the evidence audit.</div>
<h2>Comparison</h2><ul>{comparisons}</ul>
<p>Primary error averages rounds 2–4, then averages seeds within each system. Four designed systems and two seeds are a small descriptive study; these results do not establish broad superiority. The new method remains optional.</p>
<img alt="Per-system error curves for all three policies" src="data:image/png;base64,{base64.b64encode(chart.read_bytes()).decode()}">
<small>Lines show the mean of two noise seeds; shaded regions show their range, not confidence intervals. Each panel has its own logarithmic vertical scale.</small>
<h2>All outcomes</h2><div class="scroll"><table><thead><tr><th>System</th><th>Seed</th><th>Policy</th><th>Primary NRMSE</th><th>Final NRMSE</th><th>Final evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>What this result does and does not show</h2><p>The implementation retains an acquisition signal after structural weights collapse. Positive uncertainty does not guarantee informative interventions or lower prediction error. Its regularized covariance is local and heuristic, with known noise and exact starting controls; it does not represent optimizer multimodality or parameter-bound truncation.</p>
<p>All three policies use the same model fitting and revision rules. The new model parameters include constant-force amplitude, sinusoidal sine/cosine amplitudes and frequency, or smooth-friction amplitude. Test errors never enter experiment selection.</p>
<p>The separate Silverbox study evaluates passive prediction on measured circuit data. This simulation comparison does not establish active-learning success on physical hardware. No new physical law or state-of-the-art performance is claimed.</p>
<h2>Reproduce</h2><pre>python -m active_discovery.replication_suite --out results/new-replication
python -m active_discovery.replication_report results/new-replication</pre>
<p>The saved plan, raw records, selected parameters and frozen source snapshot accompany this report. This evaluation has now been inspected and must not be reused as untouched evidence after tuning.</p></main></html>'''
    (directory/'report.html').write_text(content,encoding='utf-8')
    (directory/'audit.json').write_text(json.dumps({'complete_unique_runs':len(runs),'frozen_source_hashes_verified':len(plan['source_sha256']),
              'controls_unique_per_run':True,'metrics_finite':True},indent=2),encoding='utf-8')
    print(directory/'report.html')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    build(parser.parse_args().directory)
