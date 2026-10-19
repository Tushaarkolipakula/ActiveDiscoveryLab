import unittest
import numpy as np
from active_discovery.extended_models import ExtendedFit, extended_covariance
from active_discovery.environment import Experiment, Protocol
from active_discovery.selection import acquisition_components


class RevisionUncertaintyContracts(unittest.TestCase):
    def test_unobserved_parameters_retain_uncertainty(self):
        covariance,rank=extended_covariance(np.zeros((10,7)),np.zeros(7),np.arange(1,8))
        np.testing.assert_allclose(covariance,np.diag(np.arange(1,8)**2/12))
        self.assertEqual(rank,0)

    def test_more_information_contracts_covariance(self):
        rng=np.random.default_rng(92); jac=rng.normal(size=(30,7))
        a,_=extended_covariance(jac,np.zeros(7),np.ones(7))
        b,_=extended_covariance(np.vstack([jac,jac]),np.zeros(7),np.ones(7))
        self.assertGreaterEqual(np.linalg.eigvalsh(np.asarray(a)-b).min(),-1e-12)

    def test_parameter_signal_survives_single_extended_model(self):
        fit=ExtendedFit('combined+periodic',[1.,.3,.4,.2],0.,.01,weight=1.,converged=True,
                        covariance=(np.eye(7)*.01).tolist(),extension='periodic',extra_parameters=[.4,.1,2.3])
        exp=Experiment(.5,.3); protocol=Protocol()
        base=acquisition_components([fit],exp,protocol)
        local=acquisition_components([fit],exp,protocol,True)
        self.assertAlmostEqual(base['total'],0.)
        self.assertGreater(local['parameter'],0.)
        sensitivity=fit.sensitivities(exp,protocol.times)
        expected=.01*np.mean(np.sum(sensitivity**2,axis=1))/protocol.noise_std**2
        self.assertAlmostEqual(local['total'],expected)
