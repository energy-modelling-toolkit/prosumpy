""" 
Base self consumption
All algorithms should have the same arguments and return all energy flows as a
dict of ndarrays
"""
import numpy as np
import pandas as pd

def base_sc(pv, demand, return_series=False):
    """ Base self consumption.
    Self consumption in the case of no battery 

    Arguments:
        pv (pd.Series): Vector of PV generation, in kW AC (i.e. after the inverter)
        demand (pd.Series): Vector of household consumption, kW
        return_series(bool): if True then the return will be a dictionary of series. Otherwise it will be a dictionary of ndarrays.
                        It is reccommended to return ndarrays if speed is an issue (e.g. for batch runs).
    Returns:
        dict: Dictionary of Time series

    """

    Nsteps = len(pv)
    
    pv_arr = pv.to_numpy()
    demand = demand.to_numpy()
    
    # PV
    pv2inv = pv_arr # AC
    pv2store = np.zeros(Nsteps)
    # Storage
    store2inv = np.zeros(Nsteps)
    # Inverter
    inv2grid = np.maximum(pv-demand,0)  # AC
    inv2load = pv_arr - inv2grid  # AC
    # Grid
    grid2load = demand - inv2load  # AC
    # Missing outputs
    res_pv = inv2grid # AC no more inverter, hence res_pv = inv2grid
    LevelOfCharge = np.zeros(Nsteps) # no more battery, charge always 0


    out = {'pv2inv': pv2inv,
            'res_pv': res_pv,
            'pv2store': pv2store,
            'inv2load': inv2load,
            'grid2load': grid2load,
            'store2inv': store2inv,
            'LevelOfCharge': LevelOfCharge,
            'inv2grid': inv2grid
            }
    
    if return_series:
        out_pd = {}
        for k, v in out.items():  # Create dictionary of pandas series with same index as the input pv
            out_pd[k] = pd.Series(v, index=pv.index)
        out = out_pd
    
    return out

# demand = pd.read_csv('../tests/data/demand_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv_1kW = pd.read_csv('../tests/data/pv_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv = pv_1kW*10.

# out = base_sc(pv, demand, return_series=False)

# param_tech = {'BatteryCapacity': 20,
#               'BatteryEfficiency': .9,
#               'InverterEfficiency': .85,
#               'timestep': .25,
#               'MaxPower': 20}

# demand = pd.read_csv('../tests/data/demand_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv_1kW = pd.read_csv('../tests/data/pv_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv = pv_1kW*10.

# out = dispatch_max_sc(pv, demand,param_tech, return_series=True)
















