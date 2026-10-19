import unittest
import numpy as np

from active_discovery.environment import Experiment, Protocol, make_experiment_api, trajectory, trajectory_sensitivities
from active_discovery.models import Fit, fit_models, local_covariance
from active_discovery.runner import discover
from active_discovery.selection import acquisition_components, candidate_pool, select_experiment, space_filling_order
from active_discovery.diagnostics import assess_evidence


class ScientificContracts(unittest.TestCase):
    def test_ambiguity_is_reported_without_asserting_unique_law(self):
        fits = [Fit('linear', [1, .2, 0, 0], 10, .01, converged=True),
                Fit('nonlinear_spring', [1, .2, .1, 0], 12, .01, converged=True)]
        evidence = assess_evidence(fits, 100, .015)
        self.assertEqual(evidence['status'], 'ambiguous')
        self.assertEqual(len(evidence['competitive_models']), 2)

    def test_gross_model_mismatch_overrides_unique_preference(self):
        fits = [Fit('linear', [1, .2, 0, 0], 10, 1., converged=True),
                Fit('nonlinear_spring', [1, .2, .1, 0], 50, 2., converged=True)]
        self.assertEqual(assess_evidence(fits, 100, .015)['status'], 'poor_fit')

    def test_fit_failure_is_not_presented_as_confident_discovery(self):
        fits = [Fit('linear', [1, .2, 0, 0], 10, .001, converged=False),
                Fit('nonlinear_spring', [1, .2, .1, 0], 50, .002, converged=True)]
        self.assertEqual(assess_evidence(fits, 100, .015)['status'], 'optimisation_warning')

    def test_zero_forcing_matches_original_simulator(self):
        times = np.linspace(0, 4, 41)
        args = ([1, .2, .5, .4], Experiment(.5, .3), times)
        np.testing.assert_array_equal(trajectory(*args), trajectory(*args, forcing=[0, 2.]))

    def test_observer_cannot_mutate_saved_discovery(self):
        protocol = Protocol()
        def corrupt_copy(step, observation):
            step['fits'].clear()
            observation.position[:] = 1e9
        run = discover(make_experiment_api([1., .2, 0, 0], protocol, 1), protocol,
                       'active', budget=1, starts=1, on_round=corrupt_copy)
        self.assertEqual(len(run['rounds'][0]['fits']), 4)
        self.assertLess(max(run['observations'][0]['position']), 2)

    def test_variational_equations_match_numerical_derivatives(self):
        coefficients = np.array([1.3, .25, .7, .4])
        experiment = Experiment(.8, -.6)
        times = np.linspace(0, 4, 41)
        position, gradients = trajectory_sensitivities(coefficients, experiment, times)
        np.testing.assert_allclose(position, trajectory(coefficients, experiment, times, precise=True), atol=3e-6)
        for index in range(4):
            delta = np.zeros(4)
            delta[index] = 1e-4
            numerical = (trajectory(coefficients+delta, experiment, times, precise=True)
                         - trajectory(coefficients-delta, experiment, times, precise=True))/(2e-4)
            np.testing.assert_allclose(gradients[:, index], numerical, atol=3e-5, rtol=3e-4)

    def test_covariance_retains_unidentified_directions(self):
        covariance, rank = local_covariance(np.zeros((10, 2)), (0, 1))
        covariance = np.array(covariance)
        self.assertEqual(rank, 0)
        self.assertGreater(covariance[0, 0], 0)
        self.assertGreater(covariance[1, 1], 0)
        np.testing.assert_array_equal(covariance[2:], 0)
        self.assertGreaterEqual(np.linalg.eigvalsh(covariance).min(), 0)

    def test_covariance_contracts_with_additional_information(self):
        jacobian = np.array([[1., .5], [.2, 1.]])
        first, _ = local_covariance(jacobian, (0, 1))
        second, _ = local_covariance(np.tile(jacobian, (10, 1)), (0, 1))
        self.assertTrue(np.all(np.linalg.eigvalsh(np.array(first)-np.array(second)) >= -1e-12))
        self.assertLess(np.trace(second), np.trace(first))

    def test_parameter_acquisition_survives_single_model_collapse(self):
        fit = Fit('linear', [1.3, .25, 0, 0], 0, 0, 1.0,
                  covariance=np.diag([.1, .1, 0, 0]).tolist())
        protocol = Protocol()
        experiment = Experiment(.9, .5)
        structural = acquisition_components([fit], experiment, protocol)
        local = acquisition_components([fit], experiment, protocol, True)
        self.assertEqual(structural['total'], 0)
        self.assertGreater(local['parameter'], 0)
        self.assertAlmostEqual(local['total'], local['structural']+local['parameter'])

    def test_integrator_matches_analytic_oscillator(self):
        times = np.linspace(0, 5, 101)
        actual = trajectory([2.0, 0, 0, 0], Experiment(0.7, 0.3), times)
        expected = 0.7*np.cos(np.sqrt(2)*times) + 0.3/np.sqrt(2)*np.sin(np.sqrt(2)*times)
        np.testing.assert_allclose(actual, expected, atol=2e-6)

    def test_seeded_measurements_are_reproducible(self):
        protocol = Protocol()
        first = make_experiment_api([1, .2, 0, 0], protocol, 7)
        second = make_experiment_api([1, .2, 0, 0], protocol, 7)
        exp = Experiment(.3, -.2)
        np.testing.assert_array_equal(first(exp).position, second(exp).position)
        self.assertFalse(np.array_equal(first(exp).position, second(Experiment(.4, -.2)).position))

    def test_controls_reject_invalid_experiments(self):
        api = make_experiment_api([1, .2, 0, 0], Protocol(), 0)
        for exp in [Experiment(1.1, 0), Experiment(float('nan'), 0)]:
            with self.assertRaises(ValueError):
                api(exp)

    def test_fitting_recovers_low_noise_linear_dynamics(self):
        protocol = Protocol(noise_std=.001)
        api = make_experiment_api([1.3, .25, 0, 0], protocol, 5)
        observations = [api(Experiment(.8, .5)), api(Experiment(-.5, .8))]
        fits = fit_models(observations, protocol.noise_std, starts=1)
        best = min(fits, key=lambda fit: fit.bic)
        self.assertEqual(best.name, 'linear')
        np.testing.assert_allclose(best.coefficients[:2], [1.3, .25], atol=.015)
        self.assertAlmostEqual(sum(fit.weight for fit in fits), 1.0)

    def test_active_prefers_informative_excitation(self):
        protocol = Protocol()
        fits = [Fit('a', [1, .2, 0, 0], 0, 0, .5),
                Fit('b', [1, .2, 1, 0], 0, 0, .5)]
        choice, score = select_experiment('active', fits, [], [Experiment(.05, 0), Experiment(1, 0)],
                                          protocol, np.random.default_rng(0))
        self.assertEqual(choice, Experiment(1, 0))
        self.assertGreater(score, 0)

    def test_systematic_is_complete_without_duplicates(self):
        pool = candidate_pool()
        self.assertEqual(set(space_filling_order(pool)), set(pool))
        self.assertEqual(len(space_filling_order(pool)), len(set(pool)))

    def test_discovery_accepts_only_measurement_callable(self):
        protocol = Protocol(noise_std=.01)
        received = []
        original = make_experiment_api([1, .2, 0, 0], protocol, 0)
        def measurement_only(exp):
            received.append(exp)
            return original(exp)
        run = discover(measurement_only, protocol, 'active', budget=2, starts=1)
        self.assertEqual(len(received), 2)
        self.assertEqual(len(set(received)), 2)
        self.assertNotIn('metrics', run)
        self.assertNotIn('truth', run)


if __name__ == '__main__':
    unittest.main()
