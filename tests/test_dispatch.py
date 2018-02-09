from prosumpy import dispatch_max_sc
import numpy as np
import pandas as pd

class TestDispatch_max(object):
    """ Contains methods for testing the validity of dispatch algorithms"""
    @classmethod
    def setup_class(cls):
        cls.param_tech = {'BatteryCapacity': 30,
                     'BatteryEfficiency': 1,
                     'InverterEfficiency': .9,
                     'timestep': 0.25,
                     'MaxPower': 45}
        cls.demand = pd.Series.from_csv('./tests/data/demand_example.csv')
        cls.pv = pd.Series.from_csv('./tests/data/pv_example.csv')
        cls.pv = cls.pv * 10
        cls.E = dispatch_max_sc(cls.pv, cls.demand, cls.param_tech)

    def test_pv_balance(self):
        E = self.E
        assert np.isclose(sum(self.pv - E['pv2inv'] - E['pv2store']),0)

    def test_demand_balance(self):
        E = self.E
        assert np.isclose(sum((E['inv2load'] + E['grid2load'] - self.demand)),0)

    def test_inv_balance(self):
        E = self.E
        assert np.isclose(sum((E['pv2inv'] + E['store2inv']) * self.param_tech['InverterEfficiency'] - E['inv2load'] - E['inv2grid']),0)

    def test_level_of_charge(self):
        assert (self.E['LevelOfCharge'] >= 0).all() and (self.E['LevelOfCharge'] <= self.param_tech['BatteryCapacity']).all()
