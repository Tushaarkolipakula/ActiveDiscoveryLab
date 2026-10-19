"""Trajectory-based candidate fitting; no differentiation of noisy positions."""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .environment import trajectory

MODEL_TERMS = {
    "linear": (0, 1),
    "nonlinear_spring": (0, 1, 2),
    "quadratic_drag": (0, 1, 3),
    "combined": (0, 1, 2, 3),
}
LOWER = np.array([0.2, 0.01, 0.0, 0.0])
UPPER = np.array([3.0, 1.2, 1.5, 1.5])


@dataclass
class Fit:
    name: str
    coefficients: list
    bic: float
    rss: float
    weight: float = 0.0
    converged: bool = False
    covariance: list | None = None
    information_rank: int | None = None

    def predict(self, experiment, times):
        return trajectory(self.coefficients, experiment, times)

    @property
    def parameter_count(self):
        return len(MODEL_TERMS[self.name])


def fit_from_record(record):
    if 'extension' in record:
        from .extended_models import ExtendedFit
        return ExtendedFit(**record)
    return Fit(**record)


def local_covariance(jacobian, terms):
    """Regularised local uncertainty, NOT a calibrated posterior covariance.

    Residual Jacobian already includes division by known sensor sigma. Work
    in coordinates scaled by parameter bound widths. A fixed precision 12*I
    caps unobserved directions at width^2/12 (uniform-box variance). This is
    a Gaussian regularisation heuristic, not a truncated uniform posterior.
    Unlike a plain pseudoinverse, null directions retain uncertainty.
    """
    indices = np.array(terms)
    widths = UPPER[indices] - LOWER[indices]
    scaled = jacobian*widths[None, :]
    precision = scaled.T@scaled + 12*np.eye(len(indices))
    local = np.linalg.solve(precision, np.eye(len(indices)))
    local = widths[:, None]*local*widths[None, :]
    full = np.zeros((4, 4))
    full[np.ix_(indices, indices)] = (local+local.T)/2
    return full.tolist(), int(np.linalg.matrix_rank(scaled))


def fit_models(history, noise_std, starts=2, seed=0):
    """BIC uses known Gaussian sensor variance; weights are tempered scores.

    These weights are NOT calibrated probabilities. Local parameter covariance
    is estimated from the residual Jacobian. Multistart fitting itself only
    mitigates optimiser failure and is not an uncertainty estimator.
    """
    if not history or starts < 1 or noise_std <= 0:
        raise ValueError("Need observations, positive noise and at least one start")
    rng = np.random.default_rng(seed)
    fits = []
    n = sum(len(obs.position) for obs in history)
    for name, terms in MODEL_TERMS.items():
        indices = np.array(terms)

        def expand(parameters):
            full = np.zeros(4)
            full[indices] = parameters
            return full

        def residual(parameters):
            full = expand(parameters)
            return np.concatenate([
                (trajectory(full, obs.experiment, obs.times) - obs.position) / noise_std
                for obs in history
            ])

        attempts = []
        for start in range(starts):
            initial = (LOWER[indices] + UPPER[indices]) / 2 if start == 0 else rng.uniform(LOWER[indices], UPPER[indices])
            result = least_squares(residual, initial, bounds=(LOWER[indices], UPPER[indices]),
                                   max_nfev=100, ftol=1e-6, xtol=1e-6, gtol=1e-6)
            attempts.append(result)
        best = min(attempts, key=lambda item: np.dot(item.fun, item.fun))
        scaled_rss = float(np.dot(best.fun, best.fun))
        covariance, rank = local_covariance(best.jac, terms)
        fits.append(Fit(name, expand(best.x).tolist(), scaled_rss + len(terms)*np.log(n),
                        scaled_rss*noise_std**2, converged=bool(best.success),
                        covariance=covariance, information_rank=rank))
    scores = np.array([fit.bic for fit in fits])
    weights = np.exp(-0.5*(scores-scores.min()) / 2.0)
    weights /= weights.sum()
    for fit, weight in zip(fits, weights):
        fit.weight = float(weight)
    return fits
