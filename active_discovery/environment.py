"""Experiment contract and simulation infrastructure."""
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class Protocol:
    duration: float = 4.0
    samples: int = 41
    noise_std: float = 0.015
    control_limit: float = 1.0

    def __post_init__(self):
        if not np.isfinite([self.duration, self.noise_std, self.control_limit]).all():
            raise ValueError("Protocol values must be finite")
        if self.duration <= 0 or self.samples < 3 or self.noise_std <= 0 or self.control_limit <= 0:
            raise ValueError("Invalid protocol")

    @property
    def times(self):
        return np.linspace(0, self.duration, self.samples)


@dataclass(frozen=True)
class Experiment:
    position: float
    velocity: float

    def validate(self, protocol: Protocol):
        if not np.isfinite([self.position, self.velocity]).all():
            raise ValueError("Controls must be finite")
        if max(abs(self.position), abs(self.velocity)) > protocol.control_limit:
            raise ValueError("Experiment outside allowed controls")


@dataclass
class Observation:
    experiment: Experiment
    times: np.ndarray
    position: np.ndarray


def trajectory(coefficients, experiment, times, *, precise=False, forcing=None):
    """Integrate x'' = -k*x - c*v - b*x^3 - d*v*abs(v).

    Coefficients are mass-normalised. This generic forward function is shared
    by environment and fitter; the latter only supplies estimated coefficients.
    """
    k, c, b, d = coefficients

    def rhs(t, state):
        x, v = state
        external = 0.0 if forcing is None else forcing[0]*np.sin(forcing[1]*t)
        return v, -k*x - c*v - b*x**3 - d*v*abs(v) + external

    result = solve_ivp(rhs, (float(times[0]), float(times[-1])),
                       [experiment.position, experiment.velocity], t_eval=times,
                       method="DOP853" if precise else "RK45",
                       rtol=1e-10 if precise else 2e-6,
                       atol=1e-12 if precise else 1e-8,
                       max_step=0.1 if precise else 0.25)
    if not result.success or result.y.shape[1] != len(times) or not np.isfinite(result.y).all():
        raise RuntimeError("Integration failed")
    return result.y[0]


def make_experiment_api(coefficients, protocol: Protocol, seed: int, forcing=None) -> Callable:
    """Return only a measurement callable; truth is captured in a closure.

    This is a software boundary, not a security sandbox. Each strategy gets
    its own identically seeded API for paired per-round measurement noise.
    """
    truth = np.asarray(coefficients, dtype=float).copy()
    if truth.shape != (4,) or not np.isfinite(truth).all() or np.any(truth < 0):
        raise ValueError("Expected four finite nonnegative coefficients")
    rng = np.random.default_rng(seed)

    def measure(experiment: Experiment):
        experiment.validate(protocol)
        clean = trajectory(truth, experiment, protocol.times, precise=True, forcing=forcing)
        noisy = clean + rng.normal(0, protocol.noise_std, protocol.samples)
        return Observation(experiment, protocol.times, noisy)

    return measure


def trajectory_sensitivities(coefficients, experiment, times):
    """Position and derivatives with respect to (k, c, b, d).

    Integrate variational equations alongside the state. Initial controls do
    not depend on model coefficients, so initial sensitivities are zero.
    """
    k, c, b, d = coefficients

    def rhs(t, state):
        x, v = state[:2]
        sx, sv = state[2:6], state[6:10]
        ax = -k - 3*b*x*x
        av = -c - 2*d*abs(v)
        forcing = np.array([-x, -v, -x**3, -v*abs(v)])
        return np.concatenate(([v, -k*x-c*v-b*x**3-d*v*abs(v)],
                               sv, ax*sx+av*sv+forcing))

    initial = np.zeros(10)
    initial[:2] = [experiment.position, experiment.velocity]
    result = solve_ivp(rhs, (float(times[0]), float(times[-1])), initial,
                       t_eval=times, rtol=2e-6, atol=1e-8, max_step=.25)
    if not result.success or result.y.shape[1] != len(times) or not np.isfinite(result.y).all():
        raise RuntimeError("Sensitivity integration failed")
    return result.y[0], result.y[2:6].T
