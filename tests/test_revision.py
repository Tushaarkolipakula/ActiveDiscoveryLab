import unittest
import numpy as np

from active_discovery.environment import Experiment, Protocol
from active_discovery.extended_models import ExtendedFit, extended_trajectory, reweight
from active_discovery.models import Fit, fit_from_record
from active_discovery.diagnostics import assess_evidence
from dataclasses import asdict


class RevisionContracts(unittest.TestCase):
    def test_extended_gradients_match_finite_differences(self):
        times = np.linspace(0, 2, 21)
        exp = Experiment(.5, .3)
        for kind, extra in [('bias', [.2]), ('periodic', [.4, .1, 2.3]), ('dry_friction', [.1])]:
            parameters = np.array([1.1, .3, .4, .2]+extra)
            _, jac = extended_trajectory(parameters, kind, exp, times, True)
            for index in range(len(parameters)):
                delta = np.zeros(len(parameters)); delta[index] = 1e-4
                numeric = (extended_trajectory(parameters+delta, kind, exp, times)
                           - extended_trajectory(parameters-delta, kind, exp, times))/(2e-4)
                np.testing.assert_allclose(jac[:, index], numeric, atol=2e-4, rtol=3e-3)

    def test_extended_record_roundtrip_preserves_predictions(self):
        fit = ExtendedFit('combined+periodic', [1., .3, .4, .2], 5., .01,
                          converged=True, extension='periodic', extra_parameters=[.5, .1, 2.3])
        restored = fit_from_record(asdict(fit))
        self.assertEqual(restored.parameter_count, 7)
        np.testing.assert_array_equal(fit.predict(Experiment(.5, .4), Protocol().times),
                                      restored.predict(Experiment(.5, .4), Protocol().times))

    def test_expansion_competes_with_original_candidates(self):
        base = Fit('linear', [1., .3, 0, 0], 10., .02, converged=True)
        extra = ExtendedFit('combined+bias', [1., .3, 0, 0], 20., .01,
                            converged=True, extension='bias', extra_parameters=[.1])
        reweight([base, extra])
        self.assertGreater(base.weight, extra.weight)
        self.assertAlmostEqual(base.weight+extra.weight, 1)
        self.assertEqual(assess_evidence([base, extra], 100, .015)['status'], 'preferred')


if __name__ == '__main__':
    unittest.main()
