from prosumpy import dispatch_max_sc
import numpy as np
import pandas as pd

import pytest
from collections import namedtuple

@pytest.fixture(scope="session", autouse=True)
def data():
    Data = namedtuple('data', ['pv', 'demand', 'param_tech'])
    param_tech = {'BatteryCapacity': 30,
                 'BatteryEfficiency': 1,
                 'InverterEfficiency': .9,
                 'timestep': 0.25,
                 'MaxPower': 45}
    demand = pd.read_csv('./tests/data/demand_example.csv', index_col=0, header=None, squeeze=True)
    pv = pd.read_csv('./tests/data/pv_example.csv', index_col=0, header=None, squeeze=True)
    pv = pv * 10
    return Data(pv, demand, param_tech)

@pytest.fixture(scope='module', params=[dispatch_max_sc])
def model_results(request, data):
    return request.param(data.pv, data.demand, data.param_tech)


# Tests to validate that any dispatch strategy is valid.
# All node balances have to be equal to  zero
def test_pv_balance(data, model_results):
    E = model_results
    assert np.isclose(sum(data.pv - E['pv2inv'] - E['pv2store']),0)

def test_demand_balance(data, model_results):
    E = model_results
    assert np.isclose(sum((E['inv2load'] + E['grid2load'] - data.demand)),0)

def test_inv_balance(data, model_results):
    E = model_results
    assert np.isclose(sum((E['pv2inv'] + E['store2inv']) * data.param_tech['InverterEfficiency'] - E['inv2load'] - E['inv2grid']),0)

# The level of charge at any timestep must be lower that the battery capacity
def test_level_of_charge(data, model_results):
    E = model_results
    assert (E['LevelOfCharge'] >= 0).all() and (E['LevelOfCharge'] <=  data.param_tech['BatteryCapacity']).all()
