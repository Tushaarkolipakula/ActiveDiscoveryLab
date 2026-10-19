"""Transparent evidence flags, not calibrated confidence or a safety guarantee."""
from scipy.stats import chi2

from .models import MODEL_TERMS


def assess_evidence(fits, observations_count, noise_std, competitive_delta=6.0):
    ordered = sorted(fits, key=lambda fit: fit.bic)
    best = ordered[0]
    competitive = [fit.name for fit in ordered if fit.bic-best.bic <= competitive_delta]
    degrees = max(1, observations_count-best.parameter_count)
    residual_ratio = best.rss/(noise_std**2*degrees)
    tail = float(chi2.sf(best.rss/noise_std**2, degrees))
    if not all(fit.converged for fit in fits):
        status = 'optimisation_warning'
        message = 'At least one candidate fit did not converge. Model comparison may be unreliable.'
    elif tail < .001:
        status = 'poor_fit'
        message = 'Even the preferred equation leaves unusually large residuals. The candidate family or noise assumptions may be wrong.'
    elif len(competitive) > 1:
        status = 'ambiguous'
        message = 'Several equations remain competitive. The current observations do not strongly favour a unique structure.'
    else:
        status = 'preferred'
        message = 'One equation is favoured within the supplied candidate family. This is not proof that it is the true law.'
    return {'status': status, 'message': message, 'competitive_models': competitive,
            'bic_gap': float(ordered[1].bic-best.bic) if len(ordered) > 1 else None,
            'residual_ratio': float(residual_ratio), 'approximate_residual_tail': tail,
            'competitive_delta': competitive_delta,
            'caveat': 'Heuristic diagnostics; fitted boundaries, adaptive experiments and repeated looks limit calibration.'}
