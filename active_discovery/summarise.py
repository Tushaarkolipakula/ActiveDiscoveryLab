"""Descriptive pilot summary. No hypothesis test or superiority claim."""
import argparse
import json
from pathlib import Path

import numpy as np


def summarise(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    runs = [json.loads((directory/name).read_text(encoding='utf-8')) for name in manifest['runs']]
    lines = ['# Development pilot results', '',
             'These are development fixtures, not untouched final-test systems. Two seeds per system are insufficient for a reliable superiority claim.', '',
             '| Strategy | Runs | Mean NRMSE after 2 experiments | Mean final NRMSE | Median final NRMSE | Correct final structures |',
             '|---|---:|---:|---:|---:|---:|']
    for strategy in manifest['strategies']:
        group = [r for r in runs if r['strategy'] == strategy]
        errors = [r['metrics'][-1]['normalised_rmse'] for r in group]
        early = [r['metrics'][min(1, len(r['metrics'])-1)]['normalised_rmse'] for r in group]
        correct = sum(r['metrics'][-1]['structure_correct'] for r in group)
        lines.append(f'| {strategy} | {len(group)} | {np.mean(early):.5f} | {np.mean(errors):.5f} | {np.median(errors):.5f} | {correct}/{len(group)} |')
    lines.extend(['', '## Paired final prediction error', '',
                  'A lower error in one pair is descriptive, not a statistically established win.', ''])
    lookup = {(r['system'], r['seed'], r['strategy']): r for r in runs}
    for baseline in ['random', 'systematic']:
        pairs = [(r, lookup.get((r['system'], r['seed'], baseline))) for r in runs if r['strategy'] == 'active']
        pairs = [(a, b) for a, b in pairs if b is not None]
        if pairs:
            differences = [a['metrics'][-1]['normalised_rmse']-b['metrics'][-1]['normalised_rmse'] for a, b in pairs]
            lines.append(f'- Active has lower final NRMSE than {baseline} in {sum(d < 0 for d in differences)}/{len(pairs)} pairs; mean paired difference (active minus baseline): {np.mean(differences):.5f}.')
    failures = sum(not f['converged'] for r in runs for step in r['rounds'] for f in step['fits'])
    lines.extend(['', f'Candidate fits with unsuccessful optimiser termination: {failures}.', '',
                  'Next: inspect individual learning curves and acquisition scores, add parameter uncertainty, and freeze a larger final evaluation before making claims.'])
    result = '\n'.join(lines)+'\n'
    (directory/'SUMMARY.md').write_text(result, encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(summarise(parser.parse_args().directory))
