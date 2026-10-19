"""Frozen, small descriptive comparison of finite-library revision policies."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from .environment import Protocol
from .revision import discover_revision
POLICIES = ('fixed_active', 'always_active', 'revision_active', 'revision_random')
from .revision_world import make_revision_api, evaluate_revision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/revision-001'))
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('Use an empty output directory to preserve evidence.')
    args.out.mkdir(parents=True, exist_ok=True)
    cases = [
        ('control', [1.45,.22,.65,.28], 'none', []),
        ('periodic', [.9,.4,.25,.18], 'periodic', [.35,-.12,3.1]),
        ('bias', [1.6,.25,.3,.45], 'bias', [-.25]),
        ('dry', [1.2,.35,.55,.12], 'dry_friction', [.16]),
        ('outside-grammar', [1.3,.2,.45,.25], 'chirp', [.4,1.3,.7]),
    ]
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(),
            'cases': [{'id': i, 'coefficients': c, 'extra': {'kind': k, 'values': v}} for i,c,k,v in cases],
            'policies': list(POLICIES), 'budget': 4, 'starts': 2, 'seed': 73,
            'noise_seed': 10073, 'test_seed': 8711, 'test_count': 30,
            'protocol': asdict(Protocol()),
            'primary_metric': 'Final held-out trajectory NRMSE, separately for each case',
            'limitations': 'One seed and one system per mechanism; descriptive evidence only. Frozen before runs; consumed after inspection.',
            'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}
    (args.out/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    index = []
    for case in plan['cases']:
        for policy in POLICIES:
            protocol = Protocol(**plan['protocol'])
            started = time.perf_counter()
            run = discover_revision(make_revision_api(case, protocol, plan['noise_seed']), protocol,
                                    policy, plan['budget'], plan['seed'], plan['starts'])
            run['learning_seconds'] = time.perf_counter()-started
            run['metrics'] = evaluate_revision(run, case, protocol, plan['test_seed'], plan['test_count'])
            run.update({'case': case['id'], 'protocol': plan['protocol'], 'truth': case})
            filename = f"{case['id']}_{policy}.json"
            (args.out/filename).write_text(json.dumps(run, indent=2), encoding='utf-8')
            index.append(filename)
            (args.out/'index.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
            print(f"{len(index)}/20 {case['id']} {policy}: NRMSE={run['metrics'][-1]['normalised_rmse']:.5f}", flush=True)
    write_report(args.out)


def write_report(directory):
    directory = Path(directory)
    index = json.loads((directory/'index.json').read_text())
    lines = ['# Finite-library revision: measured evidence', '',
             'Four policies, five designed systems, one seed per system. All policies get four experiments. '
             'This is a descriptive stress test, not proof of broad superiority or unrestricted scientific discovery.', '',
             '| System | Policy | Final NRMSE | Selected model | Evidence | Candidate fits | Seconds |',
             '|---|---|---:|---|---|---:|---:|']
    for filename in index:
        run = json.loads((directory/filename).read_text())
        last = run['rounds'][-1]
        lines.append(f"| {run['case']} | {run['strategy']} | {run['metrics'][-1]['normalised_rmse']:.5f} | {last['best_model']} | {last['evidence']['status']} | {run['candidate_fit_count']} | {run['learning_seconds']:.1f} |")
    lines += ['', 'NRMSE uses 30 unseen initial conditions. Test observations never enter fitting or selection. '
              'Candidate fits count model optimizations, not equal-cost operations; extended models cost more. '
              'The threshold uses known simulator noise and is heuristic.', '',
              'The expanded library contains constant bias, fixed-frequency sinusoidal drive, and smooth dry friction. '
              'The chirp case remains outside this grammar. Time and forcing phase reset for every experiment. '
              'The selected structure can be wrong even when prediction error is low. '
              'Inspect raw records, convergence and ambiguity before making a resume claim.']
    (directory/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
