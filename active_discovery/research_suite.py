"""Frozen multi-system evaluation. Do not tune on its outcomes."""
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

from .environment import Protocol, make_experiment_api
from .evaluation import evaluate
from .runner import discover

STRATEGIES = ['random', 'systematic', 'active']


def make_plan():
    rng = np.random.default_rng(20261018)
    cases = []
    for family, terms in [('linear', ()), ('nonlinear_spring', (2,)), ('quadratic_drag', (3,)), ('combined', (2, 3))]:
        for index in range(2):
            coefficients = [float(rng.uniform(.6, 2.2)), float(rng.uniform(.12, .65)), 0., 0.]
            for term in terms:
                coefficients[term] = float(rng.uniform(.35, 1.2))
            cases.append({'id': f'{family}-{index+1}', 'family': family, 'coefficients': coefficients,
                          'protocol': asdict(Protocol(noise_std=.015 if index == 0 else .03,
                                                      control_limit=1.0 if index == 0 else .5)),
                          'seeds': [100, 101], 'forcing': None, 'split': 'frozen_evaluation'})
    for index, forcing in enumerate([[.5, 2.8], [.8, 1.7]]):
        cases.append({'id': f'mismatch-{index+1}', 'family': 'outside_candidate_library',
                      'coefficients': [1.2, .3, .5, .4], 'protocol': asdict(Protocol()),
                      'seeds': [100], 'forcing': forcing, 'split': 'mismatch_stress'})
    return {'created_utc': datetime.now(timezone.utc).isoformat(), 'cases': cases,
            'strategies': STRATEGIES, 'budget': 4, 'starts': 2, 'test_count': 50,
            'test_seed': 73193, 'generator_seed': 20261018,
            'primary_metric': 'Mean held-out NRMSE across rounds 2,3,4, averaged over seeds within each case',
            'inference_unit': 'case (8 in-family systems); seed replicates are not independent systems',
            'diagnostic_thresholds': {'competitive_delta_bic': 6., 'residual_tail_warning': .001},
            'status': 'Frozen evaluation; once inspected it is consumed and cannot serve as a fresh test after tuning.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/research-001'))
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('Use a fresh directory to preserve evidence.')
    args.out.mkdir(parents=True, exist_ok=True)
    plan = make_plan()
    plan['source_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    plan['versions'] = {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__}
    (args.out/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    index = []
    for case in plan['cases']:
        protocol = Protocol(**case['protocol'])
        for seed in case['seeds']:
            for strategy in STRATEGIES:
                started = time.perf_counter()
                measure = make_experiment_api(case['coefficients'], protocol, seed+10000, forcing=case['forcing'])
                run = discover(measure, protocol, strategy, plan['budget'], seed, plan['starts'])
                run['learning_seconds'] = time.perf_counter()-started
                run['metrics'] = evaluate(run, case['coefficients'], protocol, plan['test_seed'], plan['test_count'], case['forcing'])
                run.update({'case': case['id'], 'split': case['split'], 'family': case['family'], 'protocol': case['protocol']})
                filename = f"{case['id']}_{seed}_{strategy}.json"
                (args.out/filename).write_text(json.dumps(run, indent=2), encoding='utf-8')
                index.append(filename)
                (args.out/'index.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
                print(f"{len(index)}/54 {case['id']} seed={seed} {strategy}: error={run['metrics'][-1]['normalised_rmse']:.4f}, evidence={run['rounds'][-1]['evidence']['status']}", flush=True)
    from .research_report import write_report
    print(write_report(args.out), flush=True)


if __name__ == '__main__':
    main()
