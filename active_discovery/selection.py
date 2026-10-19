"""Selection sees candidate models and observed history, never ground truth."""
import numpy as np

from .environment import Experiment, trajectory_sensitivities


def acquisition_components(fits, experiment, protocol, include_parameters=False):
    weights = np.array([fit.weight for fit in fits])
    predictions = np.stack([fit.predict(experiment, protocol.times) for fit in fits])
    mean = np.sum(weights[:, None]*predictions, axis=0)
    structural = float(np.mean(np.sum(weights[:, None]*(predictions-mean)**2, axis=0)))
    parameter = 0.0
    if include_parameters:
        for fit, weight in zip(fits, weights):
            if weight == 0:
                continue
            if fit.covariance is None:
                raise ValueError("Parameter-aware selection requires covariance estimates")
            if hasattr(fit, 'sensitivities'):
                sensitivity = fit.sensitivities(experiment, protocol.times)
            else:
                _, sensitivity = trajectory_sensitivities(fit.coefficients, experiment, protocol.times)
            covariance = np.asarray(fit.covariance)
            diagonal = np.einsum('ti,ij,tj->t', sensitivity, covariance, sensitivity)
            parameter += float(weight*np.mean(np.maximum(diagonal, 0)))
    return {"structural": structural/protocol.noise_std**2,
            "parameter": parameter/protocol.noise_std**2,
            "total": (structural+parameter)/protocol.noise_std**2}


def candidate_pool(limit=1.0, size=5):
    values = np.linspace(-limit, limit, size)
    return [Experiment(float(x), float(v)) for x in values for v in values
            if abs(x) + abs(v) > 1e-12]


def space_filling_order(pool):
    """Predetermined farthest-first sequence, independent of observations."""
    remaining = list(pool)
    selected = [remaining.pop(0)]
    while remaining:
        distances = [min((p.position-q.position)**2 + (p.velocity-q.velocity)**2
                         for q in selected) for p in remaining]
        selected.append(remaining.pop(int(np.argmax(distances))))
    return selected


def select_experiment(strategy, fits, history, pool, protocol, rng):
    used = {obs.experiment for obs in history}
    available = [p for p in pool if p not in used]
    if not available:
        raise ValueError("Candidate pool exhausted")
    if strategy == "random":
        return available[int(rng.integers(len(available)))], None
    if strategy == "systematic":
        return next(p for p in space_filling_order(pool) if p not in used), None
    if strategy == 'active_information':
        from .information import information_components
        scores = [information_components(fits, experiment, protocol)['total'] for experiment in available]
        index = int(np.argmax(scores))
        return available[index], scores[index]
    if strategy not in {"active", "active_local"}:
        raise ValueError(f"Unknown strategy: {strategy}")
    scores = [acquisition_components(fits, experiment, protocol,
                                    include_parameters=strategy == "active_local")["total"]
              for experiment in available]
    # Stable tie break. This is structural disagreement, not information gain.
    index = int(np.argmax(scores))
    return available[index], scores[index]
