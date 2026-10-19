import unittest
import numpy as np
from active_discovery.information import gaussian_information


class InformationContracts(unittest.TestCase):
    def test_scalar_matches_analytic_entropy_reduction(self):
        self.assertAlmostEqual(gaussian_information([[4.]],[[3.]],2.),.5*np.log(10.))

    def test_parameter_rescaling_does_not_change_score(self):
        c=np.array([[2.,.3],[.3,1.]])
        j=np.array([[1.,2.],[3.,-.5],[.2,4.]])
        a=np.diag([100.,.01])
        self.assertAlmostEqual(gaussian_information(c,j,.2),gaussian_information(a@c@a.T,j@np.linalg.inv(a),.2),places=9)

    def test_diverse_measurements_beat_redundant_equal_variance(self):
        redundant=np.array([[1.,0.],[1.,0.]])
        diverse=np.eye(2)
        self.assertGreater(gaussian_information(np.eye(2),diverse,1.),gaussian_information(np.eye(2),redundant,1.))

    def test_singular_covariance_and_invalid_inputs(self):
        self.assertAlmostEqual(gaussian_information(np.zeros((2,2)),np.ones((4,2)),.1),0.)
        with self.assertRaises(ValueError): gaussian_information([[-1.]],[[1.]],1.)
        with self.assertRaises(ValueError): gaussian_information([[1.]],[[1.]],0.)
