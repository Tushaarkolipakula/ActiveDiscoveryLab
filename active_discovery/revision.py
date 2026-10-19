"""Detect inadequacy, open a fixed grammar, intervene, validate later."""
from dataclasses import asdict
import copy
import numpy as np

from .diagnostics import assess_evidence
from .environment import Experiment
from .extended_models import fit_extensions, reweight
from .models import fit_models
from .selection import candidate_pool, select_experiment, acquisition_components

POLICIES = ('fixed_active', 'always_active', 'revision_active', 'revision_random', 'revision_local')


def discover_revision(measure, protocol, policy='revision_active', budget=4, seed=0, starts=2, on_round=None):
    if policy not in POLICIES:
        raise ValueError('Unknown revision policy')
    pool = candidate_pool(protocol.control_limit)
    if not 2 <= budget <= len(pool)+1:
        raise ValueError('Revision requires a valid budget of at least two')
    history, rounds = [], []
    rng = np.random.default_rng(seed)
    experiment = Experiment(.15*protocol.control_limit, 0.)
    acquisition, components = None, None
    opened = policy == 'always_active'
    candidate_fit_count = 0
    for step in range(budget):
        history.append(measure(experiment))
        base = fit_models(history, protocol.noise_std, starts, seed+step)
        candidate_fit_count += len(base)
        base_evidence = assess_evidence(base, len(history)*protocol.samples, protocol.noise_std)
        best_base = min(base, key=lambda fit: fit.bic)
        triggered = (not opened and policy.startswith('revision_') and step >= 1
                     and best_base.converged and base_evidence['approximate_residual_tail'] < .001)
        opened = opened or triggered
        candidates = base[:]
        if opened:
            combined = next(f for f in base if f.name == 'combined')
            candidates += fit_extensions(history, protocol.noise_std, combined, starts)
            candidate_fit_count += 3
        reweight(candidates)
        best = min(candidates, key=lambda fit: fit.bic)
        evidence = assess_evidence(candidates, len(history)*protocol.samples, protocol.noise_std)
        revision = {'library_open': opened, 'triggered_now': triggered,
                    'base_evidence': base_evidence, 'candidate_count': len(candidates),
                    'selected_extension': getattr(best, 'extension', None),
                    'cumulative_candidate_fits': candidate_fit_count,
                    'reason': ('Persistent poor fit after at least two observations opened the finite extension grammar.'
                               if triggered else 'Library remains open.' if opened else 'Original library retained.')}
        record = {'experiments': step+1, 'chosen_experiment': asdict(experiment),
                  'acquisition_score': acquisition, 'acquisition_components': components,
                  'best_model': best.name, 'fits': [asdict(f) for f in candidates],
                  'evidence': evidence, 'revision': revision}
        rounds.append(record)
        if on_round:
            on_round(copy.deepcopy(record), copy.deepcopy(history[-1]))
        if step+1 < budget:
            strategy = 'random' if policy == 'revision_random' else 'active_local' if policy == 'revision_local' else 'active'
            experiment, acquisition = select_experiment(strategy, candidates, history, pool, protocol, rng)
            components = acquisition_components(candidates, experiment, protocol, include_parameters=strategy == 'active_local') if strategy != 'random' else None
    observations = [{'experiment': asdict(o.experiment), 'times': o.times.tolist(), 'position': o.position.tolist()} for o in history]
    return {'strategy': policy, 'seed': seed, 'rounds': rounds, 'observations': observations,
            'candidate_fit_count': candidate_fit_count}
