import unittest
import numpy as np
from active_discovery.silverbox import predict, score


class FreeRunningContracts(unittest.TestCase):
    def test_scoring_outputs_cannot_change_predictions(self):
        model={'coefficients':[.8,0.,.1,0.,0.], 'scale_u':1., 'scale_y':1., 'cubic':False}
        u=np.ones(100)
        first=np.ones(100); first[50:]=np.linspace(0.,1.,50)
        second=first.copy(); second[50:]+=100.
        metrics_a,a=score(model,u,first)
        metrics_b,b=score(model,u,second)
        np.testing.assert_array_equal(a,b)
        self.assertNotEqual(metrics_a['rmse_volts'],metrics_b['rmse_volts'])

    def test_divergence_is_reported_without_clipping(self):
        model={'coefficients':[2.,0.,0.,0.,0.], 'scale_u':1., 'scale_y':1., 'cubic':False}
        self.assertIsNone(predict(model,np.zeros(100),np.ones(50)))

    def test_full_test_outputs_rejected_by_prediction_api(self):
        with self.assertRaises(ValueError):
            predict({},np.zeros(100),np.zeros(100))
