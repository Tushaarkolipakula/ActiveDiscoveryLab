"""Frozen five-policy design comparison; resumable only with identical source."""
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
from .revision_world import make_revision_api,evaluate_revision

POLICIES=['revision_random','revision_systematic','revision_active','revision_local','revision_information']


def source_files():
    return {p.name:p.read_bytes() for p in Path(__file__).parent.glob('*.py')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('results/design-001'))
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args(); files=source_files()
    hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    if args.resume:
        plan=json.loads((args.out/'plan.json').read_text())
        if hashes!=plan['source_sha256']: parser.error('Source changed; cannot resume frozen study.')
    else:
        if args.out.exists() and any(args.out.iterdir()): parser.error('Use a fresh output directory or --resume.')
        args.out.mkdir(parents=True,exist_ok=True)
        specs=[('bias-new',[1.45,.3,.5,.35],'bias',[-.36]),
               ('periodic-new',[1.1,.33,.45,.25],'periodic',[.32,-.18,1.85]),
               ('friction-new',[.95,.26,.7,.3],'dry_friction',[.13])]
        plan={'created_utc':datetime.now(timezone.utc).isoformat(),
              'cases':[{'id':i,'coefficients':c,'extra':{'kind':k,'values':v}} for i,c,k,v in specs],
              'seeds':[419,523],'policies':POLICIES,'budget':4,'starts':2,
              'protocol':asdict(Protocol(noise_std=.02)), 'test_seed':81023,'test_count':50,
              'primary_metric':'Mean held-out NRMSE rounds 2–4, then paired seed average within system',
              'hypothesis':'Local Gaussian information may reduce redundant measurement directions compared with predictive variance; no superiority assumed.',
              'limitations':'Three designed extension systems and two noise seeds; no new control or out-of-grammar calibration in this study.',
              'source_sha256':hashes,
              'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
        (args.out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
        snapshot=args.out/'source';snapshot.mkdir()
        for name,content in files.items(): (snapshot/name).write_bytes(content)
    index=[]
    total=len(plan['cases'])*len(plan['seeds'])*len(plan['policies'])
    for case in plan['cases']:
        for seed in plan['seeds']:
            for policy in plan['policies']:
                name=f"{case['id']}_{seed}_{policy}.json";path=args.out/name
                if not path.exists():
                    protocol=Protocol(**plan['protocol']);started=time.perf_counter()
                    run=discover_revision(make_revision_api(case,protocol,seed+10000),protocol,policy,plan['budget'],seed,plan['starts'])
                    run['learning_seconds']=time.perf_counter()-started
                    run['metrics']=evaluate_revision(run,case,protocol,plan['test_seed'],plan['test_count'])
                    run.update(case=case['id'],protocol=plan['protocol'],truth=case)
                    temporary=path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(run,indent=2),encoding='utf-8');temporary.replace(path)
                else:
                    run=json.loads(path.read_text())
                    if (run['case'],run['seed'],run['strategy'])!=(case['id'],seed,policy):
                        raise ValueError('Existing record has a different identity.')
                index.append(name)
                temporary=args.out/'index.tmp';temporary.write_text(json.dumps(index,indent=2),encoding='utf-8');temporary.replace(args.out/'index.json')
                print(f"{len(index)}/{total} {case['id']} seed={seed} {policy}: final={run['metrics'][-1]['normalised_rmse']:.5f}",flush=True)
    print('Complete. Generate the evidence report with active_discovery.design_report.',flush=True)


if __name__=='__main__': main()
