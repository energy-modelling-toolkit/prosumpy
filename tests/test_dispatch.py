from prosumpy import dispatch_max_sc, dispatch_max_sc_grid_pf
import numpy as np
import pandas as pd

import pytest
from collections import namedtuple

@pytest.fixture(scope="session")
def data():
    Data = namedtuple('data', ['pv', 'demand', 'param_tech'])
    param_tech = {'BatteryCapacity': 10,
                 'BatteryEfficiency': .5,
                 'InverterEfficiency': .5,
                 'timestep': 0.25,
                 'MaxPower': 45}
    demand = pd.read_csv('./tests/data/demand_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
    pv = pd.read_csv('./tests/data/pv_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
    pv = pv * 10
    return Data(pv, demand, param_tech)

@pytest.fixture(scope='module',
                params=[dispatch_max_sc, dispatch_max_sc_grid_pf], # Enter here the strategies to be tested
                ids=['max_selfconsume', 'perfect_forecast'])
def model_results(request, data):
    return request.param(data.pv, data.demand, data.param_tech)


# The following fucntions are tests to validate that any dispatch strategy is valid.
# All node balances have to be equal to zero at any given timestep

# All flows must be positive
def test_positive_flows(model_results):
    E = model_results
    for i, v in E.items():
        assert (v > -1E-4).all()

def test_pv_balance(data, model_results):
    E = model_results
    a = pd.DataFrame([data.pv,
    (E['pv2inv'] + E['pv2store'])])
    assert np.allclose(data.pv,
                       (E['pv2inv'] + E['pv2store']) )

def test_demand_balance(data, model_results):
    E = model_results
    assert np.allclose(E['inv2load'] + E['grid2load'],
                      data.demand)

def test_inv_balance(data, model_results):
    E = model_results
    assert np.allclose((E['pv2inv'] + E['store2inv']) * data.param_tech['InverterEfficiency'],
                      E['inv2load'] + E['inv2grid'])

def test_battery_balance(data, model_results):
    E = model_results
    Ein = E['pv2store'].values + E['LevelOfCharge'].shift(1).values / data.param_tech['timestep']
    Eout = E['store2inv'].values + E['LevelOfCharge'].values / data.param_tech['timestep']
    a = pd.DataFrame([Ein, Eout, Ein-Eout]).T
    assert np.allclose(Ein[1:], Eout[1:])


# The level of charge at any timestep must be lower that the battery capacity
def test_level_of_charge(data, model_results):
    E = model_results
    assert (E['LevelOfCharge'] >= 0).all()
    assert (E['LevelOfCharge'] <=  data.param_tech['BatteryCapacity']).all()

# The total energy residue must be zero
def test_total_residue(data, model_results):
    E = model_results
    BatLosses = np.sum(E['store2inv'] - E['pv2store'])
    InverterLosses = (np.sum(E['inv2load'] + E['inv2grid']) - np.sum(E['pv2inv'] + E['store2inv']) )

    Ein = np.sum(data.pv.values + E['grid2load'])
    Eout = np.sum(E['inv2grid'] + data.demand.values) - BatLosses - InverterLosses

    assert np.isclose(Ein, Eout)

# You cannot import and export to grid at the same time:
# The product of import and export to grid has to be zero at any given moment
def test_grid_in_out(model_results):
    E = model_results
    in_out = E['inv2grid'] * E['grid2load']
    assert np.allclose(in_out, 0)
