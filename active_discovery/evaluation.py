"""Evaluation is performed only after the full discovery run has ended."""
import numpy as np

from .environment import Experiment, trajectory
from .models import MODEL_TERMS


def evaluate(run, truth, protocol, test_seed=9381, test_count=12, forcing=None):
    rng = np.random.default_rng(test_seed)
    tests = [Experiment(*pair) for pair in rng.uniform(-protocol.control_limit,
                                                      protocol.control_limit, (test_count, 2))]
    reference = np.stack([trajectory(truth, exp, protocol.times, precise=True, forcing=forcing) for exp in tests])
    reference_scale = max(float(np.sqrt(np.mean(reference**2))), 1e-8)
    true_terms = tuple(i for i, value in enumerate(truth) if abs(value) > 1e-8)
    metrics = []
    for step in run["rounds"]:
        selected = next(fit for fit in step["fits"] if fit["name"] == step["best_model"])
        predicted = np.stack([trajectory(selected["coefficients"], exp, protocol.times) for exp in tests])
        rmse = float(np.sqrt(np.mean((predicted-reference)**2)))
        metrics.append({"experiments": step["experiments"], "rmse": rmse,
                        "normalised_rmse": rmse/reference_scale,
                        "structure_correct": None if forcing else MODEL_TERMS[selected["name"]] == true_terms,
                        "coefficient_l2": None if forcing else float(np.linalg.norm(np.array(selected["coefficients"])-truth))})
    return metrics
