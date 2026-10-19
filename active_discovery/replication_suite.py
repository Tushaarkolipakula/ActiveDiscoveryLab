"""New systems and multiple noise seeds: frozen parameter-aware revision comparison."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import scipy
from .environment import Protocol
from .revision import discover_revision
from .revision_world import make_revision_api, evaluate_revision

POLICIES=('revision_active','revision_random','revision_local')


def write_report(directory):
    directory=Path(directory)
    runs=[json.loads((directory/name).read_text()) for name in json.loads((directory/'index.json').read_text())]
    lines=['# Parameter-aware revision: replication','',
           'Four new designed systems × two noise seeds × three policies. Four acquired experiments per run. '
           'Primary metric: mean unseen-trajectory NRMSE at rounds 2–4. Seeds are paired within systems; '
           'four systems are too few to establish broad superiority. This is not calibrated Bayesian inference.','',
           '| System | Seed | Policy | Primary NRMSE | Final NRMSE | Evidence | Seconds |',
           '|---|---:|---|---:|---:|---|---:|']
    for r in runs:
        primary=float(np.mean([m['normalised_rmse'] for m in r['metrics'][1:]]))
        r['primary']=primary
        lines.append(f"| {r['case']} | {r['seed']} | {r['strategy']} | {primary:.5f} | {r['metrics'][-1]['normalised_rmse']:.5f} | {r['rounds'][-1]['evidence']['status']} | {r['learning_seconds']:.1f} |")
    summary={}
    for baseline in POLICIES[:2]:
        deltas=[]
        for case in sorted({r['case'] for r in runs}):
            local=np.mean([r['primary'] for r in runs if r['case']==case and r['strategy']=='revision_local'])
            other=np.mean([r['primary'] for r in runs if r['case']==case and r['strategy']==baseline])
            deltas.append(float(local-other))
        summary[baseline]={'case_mean_differences':deltas,'mean_difference':float(np.mean(deltas)),
                           'cases_improved':sum(d<0 for d in deltas),'case_count':len(deltas)}
    (directory/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines+=['','## Paired descriptive comparisons','']
    for baseline,s in summary.items():
        lines.append(f"- Local minus {baseline}: mean difference {s['mean_difference']:.5f}; lower error in {s['cases_improved']}/{s['case_count']} systems after averaging the two seeds.")
    lines+=['','Negative differences favor the new local-uncertainty policy. Each system contributes equally; '
            'seed replicates are not treated as independent systems. Runtime is observed wall time on a shared laptop, '
            'not a controlled hardware benchmark. The primary metric includes the revision-trigger round, '
            'before revised models have influenced the next intervention.', '',
            'Local covariance uses regularized residual sensitivities, including added force parameters. '
            'It retains uncertainty when structure weights collapse, but ignores multimodal fits and parameter-bound truncation. '
            'The noise level and initial controls remain known. The dry-friction family uses a fixed smooth approximation. '
            'These tests do not calibrate mismatch detection or prove physical active-learning performance. '
            'All results are retained; this evaluation is consumed once inspected.']
    (directory/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('results/replication-001'))
    args=parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()): parser.error('Use a fresh output directory.')
    args.out.mkdir(parents=True,exist_ok=True)
    specs=[('control',[1.7,.38,.4,.55],'none',[]),
           ('periodic',[1.35,.24,.65,.3],'periodic',[.42,.16,2.65]),
           ('bias',[.85,.42,.6,.2],'bias',[.32]),
           ('friction',[1.55,.2,.35,.4],'dry_friction',[.22])]
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),
          'cases':[{'id':i,'coefficients':c,'extra':{'kind':k,'values':v}} for i,c,k,v in specs],
          'seeds':[211,307],'policies':POLICIES,'budget':4,'starts':2,'test_seed':29171,'test_count':40,
          'protocol':asdict(Protocol(noise_std=.025)),
          'primary_metric':'Mean held-out NRMSE rounds 2–4; average paired noise seeds within each system',
          'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
          'status':'Frozen before running; no test feedback enters learning or method tuning.'}
    snapshot=args.out/'source';snapshot.mkdir()
    plan['source_sha256']={}
    for path in Path(__file__).parent.glob('*.py'):
        content=path.read_bytes();(snapshot/path.name).write_bytes(content)
        plan['source_sha256'][path.name]=hashlib.sha256(content).hexdigest()
    (args.out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    index=[]
    for case in plan['cases']:
        for seed in plan['seeds']:
            for policy in POLICIES:
                protocol=Protocol(**plan['protocol']);started=time.perf_counter()
                run=discover_revision(make_revision_api(case,protocol,seed+10000),protocol,policy,4,seed,2)
                run['learning_seconds']=time.perf_counter()-started
                run['metrics']=evaluate_revision(run,case,protocol,plan['test_seed'],plan['test_count'])
                run.update(case=case['id'],protocol=plan['protocol'],truth=case)
                name=f"{case['id']}_{seed}_{policy}.json"
                (args.out/name).write_text(json.dumps(run,indent=2),encoding='utf-8')
                index.append(name);(args.out/'index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
                print(f"{len(index)}/24 {case['id']} seed={seed} {policy}: final={run['metrics'][-1]['normalised_rmse']:.5f}",flush=True)
    write_report(args.out)


if __name__=='__main__': main()
