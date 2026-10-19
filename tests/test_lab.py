import unittest

from active_discovery.lab import validate_config


class LabContracts(unittest.TestCase):
    def test_valid_config_is_explicit_and_bounded(self):
        config = validate_config({'seed': 42, 'budget': 4, 'preset': 'standard', 'strategy': 'active', 'ignored': 'value'})
        self.assertEqual(set(config), {'seed', 'budget', 'preset', 'strategy'})

    def test_unbounded_or_unrecognised_work_is_rejected(self):
        base = {'seed': 42, 'budget': 4, 'preset': 'standard', 'strategy': 'active'}
        for patch in [{'budget': 1000}, {'seed': -1}, {'budget': True}, {'strategy': 'exec'}, {'preset': '../file'}]:
            with self.assertRaises(ValueError):
                validate_config({**base, **patch})


if __name__ == '__main__':
    unittest.main()
