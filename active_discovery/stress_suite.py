"""Frozen development stress suite: python -m active_discovery.stress_suite."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

CASES = [
    {"name": "reference", "noise": .015, "control_limit": 1.0},
    {"name": "noisy", "noise": .06, "control_limit": 1.0},
    {"name": "restricted", "noise": .015, "control_limit": .35},
]
STRATEGIES = ['random', 'systematic', 'active', 'active_local']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/uncertainty-001'))
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('Use a fresh output directory; completed and partial suites are preserved.')
    args.out.mkdir(parents=True, exist_ok=True)
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(), 'cases': CASES,
            'strategies': STRATEGIES, 'seeds': [20, 21], 'budget': 4,
            'systems': ['combined'], 'starts': 2, 'status': 'development only',
            'purpose': 'Compare structural-only with local parameter-aware selection. No tuning within this suite.'}
    (args.out/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    for case in CASES:
        command = [sys.executable, '-m', 'active_discovery.benchmark', '--budget', '4',
                   '--seeds', '20', '21', '--systems', 'combined', '--starts', '2',
                   '--strategies', *STRATEGIES, '--noise', str(case['noise']),
                   '--control-limit', str(case['control_limit']), '--out', str(args.out/case['name'])]
        print(f"\nCASE {case['name']}: noise={case['noise']}, control limit={case['control_limit']}", flush=True)
        subprocess.run(command, check=True)
    from .stress_report import write_stress_report
    print(write_stress_report(args.out), flush=True)


if __name__ == '__main__':
    main()
