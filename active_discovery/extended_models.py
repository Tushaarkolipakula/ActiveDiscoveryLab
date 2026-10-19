"""Finite revision grammar: bias, periodic drive, or smooth dry friction.

This is bounded library expansion, not unrestricted symbolic discovery.
Each extension augments the full four-term base; zeros can represent absent
base terms but all free coefficients incur the BIC complexity penalty.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

from .models import Fit, LOWER, UPPER

EXTRA_BOUNDS = {
    'bias': ([-1.2], [1.2]),
    'periodic': ([-1.2, -1.2, .5], [1.2, 1.2, 4.5]),
    'dry_friction': ([0.], [.8]),
}


def extended_trajectory(parameters, extension, experiment, times, sensitivities=False):
    theta = np.asarray(parameters)
    count = len(theta)
    k, c, b, d = theta[:4]

    def rhs(t, state):
        x, v = state[:2]
        extra, dv = 0., 0.
        gradient = [-x, -v, -x**3, -v*abs(v)]
        if extension == 'bias':
            extra = theta[4]
            gradient += [1.]
        elif extension == 'periodic':
            a, q, omega = theta[4:]
            sine, cosine = np.sin(omega*t), np.cos(omega*t)
            extra = a*sine + q*cosine
            gradient += [sine, cosine, t*(a*cosine-q*sine)]
        elif extension == 'dry_friction':
            tangent = np.tanh(v/.02)
            extra = -theta[4]*tangent
            dv = -theta[4]*(1-tangent**2)/.02
            gradient += [-tangent]
        else:
            raise ValueError('Unknown revision term')
        acceleration = -k*x-c*v-b*x**3-d*v*abs(v)+extra
        if not sensitivities:
            return [v, acceleration]
        sx, sv = state[2:2+count], state[2+count:]
        ds = (-k-3*b*x*x)*sx + (-c-2*d*abs(v)+dv)*sv + np.array(gradient)
        return np.concatenate(([v, acceleration], sv, ds))

    initial = np.zeros(2+2*count if sensitivities else 2)
    initial[:2] = [experiment.position, experiment.velocity]
    solution = solve_ivp(rhs, (times[0], times[-1]), initial, t_eval=times,
                         rtol=2e-6, atol=1e-8, max_step=.2)
    if not solution.success or solution.y.shape[1] != len(times) or not np.isfinite(solution.y).all():
        raise RuntimeError('Expanded-model integration failed')
    if sensitivities:
        return solution.y[0], solution.y[2:2+count].T
    return solution.y[0]


@dataclass
class ExtendedFit(Fit):
    extension: str = 'bias'
    extra_parameters: list = field(default_factory=list)

    @property
    def parameter_count(self):
        return 4+len(self.extra_parameters)

    def predict(self, experiment, times):
        return extended_trajectory(self.coefficients+self.extra_parameters, self.extension, experiment, times)

    def sensitivities(self, experiment, times):
        return extended_trajectory(self.coefficients+self.extra_parameters, self.extension, experiment, times, True)[1]


def extended_covariance(jacobian, lower, upper):
    """Same bound-scaled local regularization as base models; not a posterior."""
    widths = np.asarray(upper)-np.asarray(lower)
    scaled = np.asarray(jacobian)*widths[None, :]
    precision = scaled.T@scaled+12*np.eye(len(widths))
    covariance = widths[:, None]*np.linalg.solve(precision, np.eye(len(widths)))*widths[None, :]
    return ((covariance+covariance.T)/2).tolist(), int(np.linalg.matrix_rank(scaled))


def fit_extensions(history, noise_std, base_fit, starts=2):
    results = []
    n = sum(len(obs.position) for obs in history)
    for extension, (low, high) in EXTRA_BOUNDS.items():
        lower, upper = np.r_[LOWER, low], np.r_[UPPER, high]
        cache_theta, cache_residual, cache_jacobian = None, None, None

        def calculate(theta):
            nonlocal cache_theta, cache_residual, cache_jacobian
            if cache_theta is not None and np.array_equal(theta, cache_theta):
                return cache_residual, cache_jacobian
            residuals, jacobians = [], []
            for obs in history:
                predicted, jacobian = extended_trajectory(theta, extension, obs.experiment, obs.times, True)
                residuals.append((predicted-obs.position)/noise_std)
                jacobians.append(jacobian/noise_std)
            cache_theta = theta.copy()
            cache_residual = np.concatenate(residuals)
            cache_jacobian = np.concatenate(jacobians)
            return cache_residual, cache_jacobian

        attempts = []
        for index in range(starts):
            extra = ([.2, .05, 1.+2.5*(index % 2)] if extension == 'periodic'
                     else [.05 if extension == 'dry_friction' else (.1 if index % 2 else -.1)])
            initial = np.r_[base_fit.coefficients, extra]
            initial = np.clip(initial, lower+1e-8, upper-1e-8)
            result = least_squares(lambda p: calculate(p)[0], initial,
                                   jac=lambda p: calculate(p)[1], bounds=(lower, upper),
                                   max_nfev=120, ftol=1e-6, xtol=1e-6, gtol=1e-6)
            attempts.append(result)
        best = min(attempts, key=lambda r: r.fun@r.fun)
        scaled = float(best.fun@best.fun)
        covariance, rank = extended_covariance(best.jac, lower, upper)
        results.append(ExtendedFit(name='combined+'+extension, coefficients=best.x[:4].tolist(),
                                   bic=scaled+len(best.x)*np.log(n), rss=scaled*noise_std**2,
                                   converged=bool(best.success), extension=extension,
                                   extra_parameters=best.x[4:].tolist(), covariance=covariance,
                                   information_rank=rank))
    return results


def reweight(fits):
    scores = np.array([f.bic for f in fits])
    weights = np.exp(-.25*(scores-scores.min()))
    weights /= weights.sum()
    for fit, weight in zip(fits, weights):
        fit.weight = float(weight)
