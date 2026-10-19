"""Budgeted discovery loop, deliberately independent of evaluation."""
from dataclasses import asdict
import numpy as np

from .environment import Experiment
from .models import fit_models
from .diagnostics import assess_evidence
from .selection import acquisition_components, candidate_pool, select_experiment


def discover(measure, protocol, strategy, budget=5, seed=0, starts=2, on_round=None):
    pool = candidate_pool(protocol.control_limit)
    if budget < 1 or budget > len(pool)+1:
        raise ValueError("Budget must be between 1 and pool size plus one")
    initial = Experiment(0.15*protocol.control_limit, 0.0)
    rng = np.random.default_rng(seed)
    history, rounds = [], []
    experiment, acquisition = initial, None
    acquisition_detail = None
    for step in range(budget):
        history.append(measure(experiment))
        fits = fit_models(history, protocol.noise_std, starts, seed + step)
        best = min(fits, key=lambda fit: fit.bic)
        evidence = assess_evidence(fits, sum(len(obs.position) for obs in history), protocol.noise_std)
        rounds.append({"experiments": step+1, "chosen_experiment": asdict(experiment),
                       "acquisition_score": acquisition, "best_model": best.name,
                       "acquisition_components": acquisition_detail,
                       "evidence": evidence,
                       "fits": [asdict(fit) for fit in fits]})
        if on_round is not None:
            # Observer only: no return value is consumed by the learner.
            import copy
            on_round(copy.deepcopy(rounds[-1]), copy.deepcopy(history[-1]))
        if step+1 < budget:
            experiment, acquisition = select_experiment(strategy, fits, history, pool, protocol, rng)
            acquisition_detail = (acquisition_components(fits, experiment, protocol,
                                   include_parameters=strategy == "active_local")
                                  if strategy in {"active", "active_local"} else None)
    observations = [{"experiment": asdict(obs.experiment), "times": obs.times.tolist(),
                     "position": obs.position.tolist()} for obs in history]
    return {"strategy": strategy, "seed": seed, "rounds": rounds, "observations": observations}
