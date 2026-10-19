"""Local live laboratory. Run: python -m active_discovery.lab --port 8765."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import uuid

import numpy as np

from .diagnostics import assess_evidence
from .environment import Experiment, Protocol, make_experiment_api, trajectory
from .evaluation import evaluate
from .models import fit_from_record
from .revision import discover_revision
from .runner import discover

ROOT = Path(__file__).resolve().parent.parent
ASSET = Path(__file__).parent/'assets'/'lab.html'
JOBS = {}
LOCK = threading.Lock()


def frame_from(step, observation, protocol):
    fits = [fit_from_record(f) for f in step['fits']]
    evidence = step.get('evidence') or assess_evidence(fits, step['experiments']*protocol.samples, protocol.noise_std)
    experiment = Experiment(**observation['experiment'])
    return {**step, 'evidence': evidence, 'observation': observation,
            'predictions': [{'name': f.name, 'position': f.predict(experiment, observation['times']).tolist()} for f in fits]}


def present_run(run, protocol, truth=None, forcing=None, label='Recorded experiment', truth_extra=None):
    frames = [frame_from(step, obs, protocol) for step,obs in zip(run['rounds'], run['observations'])]
    return {'id': 'replay', 'status': 'complete', 'mode': 'recorded', 'label': label,
            'strategy': run['strategy'], 'seed': run['seed'], 'budget': len(frames),
            'frames': frames, 'metrics': run.get('metrics'), 'truth': truth, 'forcing': forcing,
            'truth_extra': truth_extra,
            'protocol': asdict(protocol), 'message': 'Recorded real computation; replaying does not rerun training.'}


def catalog():
    entries = []
    replication = ROOT/'results'/'replication-001'
    if (replication/'index.json').exists():
        names = json.loads((replication/'index.json').read_text())
        plan = json.loads((replication/'plan.json').read_text())
        cases = {c['id']: {**c, 'protocol': plan['protocol']} for c in plan['cases']}
        entries.extend((replication/name, cases[json.loads((replication/name).read_text())['case']]) for name in names)
    revision = ROOT/'results'/'revision-001'
    if (revision/'index.json').exists():
        names = json.loads((revision/'index.json').read_text())
        plan = json.loads((revision/'plan.json').read_text())
        cases = {c['id']: {**c, 'protocol': plan['protocol']} for c in plan['cases']}
        entries.extend((revision/name, cases[json.loads((revision/name).read_text())['case']]) for name in names)
    research = ROOT/'results'/'research-001'
    if (research/'index.json').exists():
        names = json.loads((research/'index.json').read_text())
        plan = json.loads((research/'plan.json').read_text())
        cases = {c['id']: c for c in plan['cases']}
        entries.extend((research/name, cases[json.loads((research/name).read_text())['case']]) for name in names)
    if entries:
        return entries
    pilot = ROOT/'results'/'pilot-001'
    if (pilot/'manifest.json').exists():
        manifest = json.loads((pilot/'manifest.json').read_text())
        return [(pilot/name, {'coefficients': manifest['systems'][json.loads((pilot/name).read_text())['system']],
                             'forcing': None, 'protocol': manifest['protocol']}) for name in manifest['runs']]
    return []


def replay_items():
    items = []
    for index, (path, case) in enumerate(catalog()):
        run = json.loads(path.read_text())
        items.append({'id': index, 'label': f"{path.parent.name} · {run.get('case', run.get('system', 'run'))} · {run['strategy']} · seed {run['seed']}"})
    return items


def replay(index):
    path, case = catalog()[index]
    run = json.loads(path.read_text())
    return present_run(run, Protocol(**case['protocol']), case['coefficients'], case.get('forcing'), path.stem, case.get('extra'))


def live_worker(job_id, config):
    try:
        rng = np.random.default_rng(config['seed'])
        family = int(rng.integers(4))
        truth = [float(rng.uniform(.7, 2.1)), float(rng.uniform(.15, .6)),
                 float(rng.uniform(.4, 1.1)) if family in (1,3) else 0.,
                 float(rng.uniform(.3, 1.)) if family in (2,3) else 0.]
        protocol = Protocol(noise_std=.06 if config['preset'] == 'noisy' else .015,
                            control_limit=.35 if config['preset'] == 'restricted' else 1.)
        forcing = [.6, 2.4] if config['preset'] == 'mismatch' else None
        with LOCK:
            JOBS[job_id]['protocol'] = asdict(protocol)

        def observe(step, observation):
            obs = {'experiment': asdict(observation.experiment), 'times': observation.times.tolist(),
                   'position': observation.position.tolist()}
            frame = frame_from(step, obs, protocol)
            with LOCK:
                if JOBS[job_id].get('cancel_requested'):
                    raise InterruptedError('Run cancelled after the current fit completed.')
                JOBS[job_id]['frames'].append(frame)

        api = make_experiment_api(truth, protocol, config['seed']+10000, forcing)
        started = time.perf_counter()
        if config['strategy'] in {'revision_active', 'revision_local'}:
            from .revision_world import evaluate_revision
            run = discover_revision(api, protocol, config['strategy'], config['budget'], config['seed'], 2, observe)
        else:
            run = discover(api, protocol, config['strategy'], config['budget'], config['seed'], 2, observe)
        run['learning_seconds'] = time.perf_counter()-started
        if config['strategy'] in {'revision_active', 'revision_local'}:
            case = {'coefficients': truth, 'extra': {'kind': 'periodic' if forcing else 'none',
                    'values': [forcing[0], 0., forcing[1]] if forcing else []}}
            run['metrics'] = evaluate_revision(run, case, protocol, 73193, 50)
        else:
            run['metrics'] = evaluate(run, truth, protocol, 73193, 50, forcing)
        run.update({'protocol': asdict(protocol), 'truth': truth, 'forcing': forcing,
                    'purpose': 'interactive demonstration, not frozen benchmark evidence'})
        directory = ROOT/'results'/'live'
        directory.mkdir(parents=True, exist_ok=True)
        (directory/f'{job_id}.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        with LOCK:
            JOBS[job_id].update({'status': 'complete', 'metrics': run['metrics'], 'truth': truth,
                                 'forcing': forcing, 'message': 'Complete. Ground truth is now available for audit.',
                                 'learning_seconds': run['learning_seconds']})
    except InterruptedError as exc:
        with LOCK:
            JOBS[job_id].update(status='cancelled', message=str(exc))
    except Exception as exc:
        with LOCK:
            JOBS[job_id].update(status='error', message=f'{type(exc).__name__}: {exc}')


def validate_config(data):
    if not isinstance(data, dict):
        raise ValueError('Expected a configuration object.')
    seed, budget = data.get('seed', 42), data.get('budget', 4)
    if type(seed) is not int or not 0 <= seed <= 1000000:
        raise ValueError('Seed must be an integer from 0 to 1000000.')
    if type(budget) is not int or not 3 <= budget <= 6:
        raise ValueError('Budget must be 3 to 6 experiments.')
    if data.get('preset') not in {'standard', 'noisy', 'restricted', 'mismatch'}:
        raise ValueError('Unknown world preset.')
    if data.get('strategy') not in {'random', 'systematic', 'active', 'active_local', 'revision_active', 'revision_local'}:
        raise ValueError('Unknown strategy.')
    return {'seed': seed, 'budget': budget, 'preset': data['preset'], 'strategy': data['strategy']}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send(self, value, status=200, content_type='application/json'):
        content = value.encode('utf-8') if isinstance(value, str) else json.dumps(value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type+'; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers(); self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == '/':
                return self.send(ASSET.read_text(encoding='utf-8').replace('__BOOTSTRAP__', 'null'), content_type='text/html')
            if parsed.path == '/api/replays':
                return self.send(replay_items())
            if parsed.path == '/api/replay':
                index = int(query.get('id', ['-1'])[0])
                if index < 0:
                    raise ValueError('Invalid replay id.')
                return self.send(replay(index))
            if parsed.path == '/api/status':
                with LOCK:
                    job = JOBS.get(query.get('id', [''])[0])
                    if job is None:
                        return self.send({'error': 'Unknown run.'}, 404)
                    return self.send(job)
            return self.send({'error': 'Not found.'}, 404)
        except (ValueError, IndexError, KeyError) as exc:
            return self.send({'error': str(exc)}, 400)

    def do_POST(self):
        allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if self.headers.get('Origin') not in allowed:
            return self.send({'error': 'Only same-origin local requests are accepted.'}, 403)
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send({'error': 'JSON required.'}, 415)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 4096:
                raise ValueError('Invalid request size.')
            data = json.loads(self.rfile.read(length))
            if self.path == '/api/cancel':
                with LOCK:
                    job = JOBS.get(data.get('id'))
                    if job is None:
                        return self.send({'error': 'Unknown run.'}, 404)
                    job['cancel_requested'] = True
                return self.send({'ok': True})
            if self.path != '/api/start':
                return self.send({'error': 'Not found.'}, 404)
            config = validate_config(data)
            with LOCK:
                if any(j['status'] == 'running' for j in JOBS.values()):
                    return self.send({'error': 'A run is already computing. Wait or cancel it first.'}, 409)
                if len(JOBS) >= 12:
                    JOBS.pop(next(iter(JOBS)))
                job_id = uuid.uuid4().hex[:12]
                JOBS[job_id] = {'id': job_id, 'status': 'running', 'mode': 'live', 'label': 'Live discovery',
                                **config, 'frames': [], 'metrics': None, 'truth': None, 'forcing': None,
                                'message': 'Measuring and fitting. No ground truth is exposed to the learner.'}
            threading.Thread(target=live_worker, args=(job_id, config), daemon=True).start()
            return self.send({'id': job_id}, 202)
        except (ValueError, TypeError, AttributeError) as exc:
            return self.send({'error': str(exc)}, 400)


def export_replay(output):
    available = catalog()
    if not available:
        raise ValueError('No completed benchmark records to export.')
    selected = []
    seen = set()
    for index, (path, _) in enumerate(available):
        run = json.loads(path.read_text())
        if run['strategy'] not in {'active', 'revision_active', 'revision_local'}:
            continue
        family = run.get('case', run.get('family', run.get('system', 'unknown')))
        evidence = run['rounds'][-1].get('evidence', {}).get('status', 'legacy')
        key = (path.parent.name, run['strategy'], family, evidence)
        if key not in seen:
            seen.add(key)
            selected.append(replay(index))
    bootstrap = json.dumps(selected).replace('<', '\\u003c')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ASSET.read_text(encoding='utf-8').replace('__BOOTSTRAP__', bootstrap), encoding='utf-8')
    print(f'Exported {len(selected)} illustrative recorded runs to {output}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--export', type=Path)
    args = parser.parse_args()
    if args.export:
        return export_replay(args.export)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Active Discovery Lab: http://127.0.0.1:{server.server_port} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
