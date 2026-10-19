"""Independent high-accuracy simulator and evaluator for revision experiments."""
import numpy as np
from scipy.integrate import solve_ivp

from .environment import Experiment, Observation
from .models import fit_from_record


def simulate_world(case, experiment, times):
    k, c, b, d = case['coefficients']
    kind, values = case['extra']['kind'], case['extra']['values']
    def rhs(t, state):
        x, v = state
        external = 0.
        if kind == 'bias':
            external = values[0]
        elif kind == 'periodic':
            external = values[0]*np.sin(values[2]*t)+values[1]*np.cos(values[2]*t)
        elif kind == 'dry_friction':
            external = -values[0]*np.tanh(v/.02)
        elif kind == 'chirp':
            external = values[0]*np.sin(values[1]*t+values[2]*t*t)
        elif kind != 'none':
            raise ValueError('Unknown world')
        return [v, -k*x-c*v-b*x**3-d*v*abs(v)+external]
    solution = solve_ivp(rhs, (times[0], times[-1]), [experiment.position, experiment.velocity],
                         t_eval=times, method='DOP853', rtol=1e-10, atol=1e-12, max_step=.08)
    if not solution.success:
        raise RuntimeError('Reference simulation failed')
    return solution.y[0]


def make_revision_api(case, protocol, seed):
    rng = np.random.default_rng(seed)
    def measure(experiment):
        experiment.validate(protocol)
        position = simulate_world(case, experiment, protocol.times)
        return Observation(experiment, protocol.times, position+rng.normal(0, protocol.noise_std, protocol.samples))
    return measure


def evaluate_revision(run, case, protocol, test_seed=8711, count=30):
    rng = np.random.default_rng(test_seed)
    experiments = [Experiment(*row) for row in rng.uniform(-protocol.control_limit, protocol.control_limit, (count, 2))]
    reference = np.stack([simulate_world(case, exp, protocol.times) for exp in experiments])
    scale = max(float(np.sqrt(np.mean(reference**2))), 1e-8)
    metrics = []
    for step in run['rounds']:
        fit = fit_from_record(next(f for f in step['fits'] if f['name'] == step['best_model']))
        predictions = np.stack([fit.predict(exp, protocol.times) for exp in experiments])
        error = float(np.sqrt(np.mean((predictions-reference)**2)))
        metrics.append({'experiments': step['experiments'], 'normalised_rmse': error/scale, 'rmse': error,
                        'extension_correct': (getattr(fit, 'extension', 'none') == case['extra']['kind'])
                        if case['extra']['kind'] != 'chirp' else None})
    return metrics
