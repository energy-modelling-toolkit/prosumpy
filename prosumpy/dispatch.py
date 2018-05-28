""" Dispatch algorithms
All algorithms should have the same arguments and return all energy flows as a
dict of ndarrays
"""
from __future__ import division
import numpy as np
import pandas as pd

def dispatch_max_sc(pv, demand, param, return_series=False):
    """ Self consumption maximization pv + battery dispatch algorithm.
    The dispatch of the storage capacity is performed in such a way to maximize self-consumption:
    the battery is charged when the PV power is higher than the load and as long as it is not fully charged.
    It is discharged as soon as the PV power is lower than the load and as long as it is not fully discharged.

    Arguments:
        pv (pd.Series): Vector of PV generation, in kW DC (i.e. before the inverter)
        demand (pd.Series): Vector of household consumption, kW
        param (dict): Dictionary with the simulation parameters:
                timestep (float): Simulation time step (in hours)
                BatteryCapacity: Available battery capacity (i.e. only the the available DOD), kWh
                BatteryEfficiency: Battery round-trip efficiency, -
                InverterEfficiency: Inverter efficiency, -
                MaxPower: Maximum battery charging or discharging powers (assumed to be equal), kW
        return_series(bool): if True then the return will be a dictionary of series. Otherwise it will be a dictionary of ndarrays.
                        It is reccommended to return ndarrays if speed is an issue (e.g. for batch runs).
    Returns:
        dict: Dictionary of Time series

    """

    bat_size_e_adj = param['BatteryCapacity']
    bat_size_p_adj = param['MaxPower']
    n_bat = param['BatteryEfficiency']
    n_inv = param['InverterEfficiency']
    timestep = param['timestep']
    # We work with np.ndarrays as they are much faster than pd.Series
    Nsteps = len(pv)
    LevelOfCharge = np.zeros(Nsteps)
    pv2store = np.zeros(Nsteps)
    #inv2grid = np.zeros(Nsteps)
    store2inv = np.zeros(Nsteps)
    grid2store = np.zeros(Nsteps) # TODO Always zero for now.

    #Load served by PV
    pv2inv = np.minimum(pv, demand / n_inv)  # DC direct self-consumption

    #Residual load
    res_load = (demand - pv2inv * n_inv)  # AC
    inv2load = pv2inv * n_inv  # AC

    #Excess PV
    res_pv = np.maximum(pv - demand/n_inv, 0)  # DC

    #PV to storage after eff losses
    pv2inv = pv2inv.values

    #first timestep = 0
    LevelOfCharge[0] = 0  # bat_size_e_adj / 2  # DC

    for i in range(1,Nsteps):
        #PV to storage
        if LevelOfCharge[i-1] >= bat_size_e_adj:  # if battery is full
                pv2store[i] = 0
        else: #if battery is not full
            if LevelOfCharge[i-1] + res_pv[i] * n_bat * timestep > bat_size_e_adj:  # if battery will be full after putting excess
                pv2store[i] = min((bat_size_e_adj - LevelOfCharge[i-1]) / timestep, bat_size_p_adj)
            else:
                pv2store[i] = min(res_pv[i] * n_bat, bat_size_p_adj)

        #Storage to load
        store2inv[i] = min(bat_size_p_adj,  # DC
                           res_load[i] / n_inv,
                           LevelOfCharge[i-1] / timestep)

        #SOC
        LevelOfCharge[i] = min(LevelOfCharge[i-1] - (store2inv[i] - pv2store[i] - grid2store[i]) * timestep,  # DC
                               bat_size_e_adj)

    pv2inv = pv2inv + res_pv - pv2store
    inv2load = inv2load + store2inv * n_inv  # AC
    inv2grid = (res_pv - pv2store) * n_inv  # AC
    grid2load = demand - inv2load  # AC

    #MaxDischarge = np.minimum(LevelOfCharge[i-1]*BatteryEfficiency/timestep,MaxPower)


    #Potential Grid to storage  # TODO: not an option for now in this strategy
    # GridPurchase = False

    out = {'pv2inv': pv2inv,
            'res_pv': res_pv,
            'pv2store': pv2store,
            'inv2load': inv2load,
            'grid2load': grid2load,
            'store2inv': store2inv,
            'LevelOfCharge': LevelOfCharge,
            'inv2grid': inv2grid
            # 'grid2store': grid2store
            }
    if not return_series:
        out_pd = {}
        for k, v in out.items():  # Create dictionary of pandas series with same index as the input pv
            out_pd[k] = pd.Series(v, index=pv.index)
        out = out_pd
    return out



def dispatch_max_sc_grid_pf(pv, demand, param_tech, return_series=False):
    """
    Battery dispatch algorithm.
    The dispatch of the storage capacity is performed in such a way to maximize self-consumption and relief the grid by
    by deferring the storage to peak hours.
    the battery is charged when the PV power is higher than the load and as long as it is not fully charged.
    It is discharged as soon as the PV power is lower than the load and as long as it is not fully discharged.

    :param pv: Vector of PV generation, in kW DC (i.e. before the inverter)
    :param demand: Vector of household consumption, kW
    :param param_tech: Dictionary with the simulation parameters:
                    timestep: Simulation time step (in hours)
                    BatteryCapacity: Available battery capacity (i.e. only the the available DOD), kWh
                    BatteryEfficiency: Battery round-trip efficiency, -
                    InverterEfficiency: Inverter efficiency, -
                    MaxPower: Maximum battery charging or discharging powers (assumed to be equal), kW

    :return: Dictionary of Time series

    """
    bat_size_e_adj = param_tech['BatteryCapacity']
    bat_size_p_adj = param_tech['MaxPower']
    n_bat = param_tech['BatteryEfficiency']
    n_inv = param_tech['InverterEfficiency']
    timestep = param_tech['timestep']

    Nsteps = len(pv)
    LevelOfCharge = np.zeros(Nsteps)
    pv2store = np.zeros(Nsteps)
    #inv2load = np.zeros(Nsteps)
    inv2grid = np.zeros(Nsteps)
    store2inv = np.zeros(Nsteps)
    grid2store = np.zeros(Nsteps) # TODO Always zero for now.

    from scipy.optimize import brentq

    def find_threshold(pv_day_load, bat_size_e):
        """Find threshold of peak shaving (kW). The electricity fed to the grid is capped by a specific threshold.
        What is above that threshold is stored in the battery. The threshold is specified in such a way so that
        the energy amount above that threshold equals to the available storage for that day.
        pv_day_load: Daily pv production
        bat_size_e: Battery size
        """

        def get_residual_peak(thres):
            shaved_peak = np.maximum(pv_day_load - thres, 0)
            return sum(shaved_peak) * param_tech['timestep'] - bat_size_e

        if sum(pv_day_load) * param_tech['timestep'] <= bat_size_e:  # if the battery can cover the whole day
            return 0
        else:
            return brentq(get_residual_peak, 0, max(pv), rtol=1e-4)

    # It is better to use vectorize operations as much as we can before looping.
    # first self consume
    # Load served by PV
    pv2inv = np.minimum(pv, demand / n_inv)  # DC direct self-consumption

    # Residual load
    res_load = (demand - pv2inv * n_inv)  # AC
    inv2load = pv2inv * n_inv  # AC
    pv2inv = pv2inv.values

    # Excess PVs
    res_pv = np.maximum(pv - demand / n_inv, 0)  # DC
    res_pv_val = res_pv.values
    Nsteps = len(demand)
    LevelOfCharge[0] = 0  # bat_size_e_adj / 2 # Initial storage is empty # DC

    # For the residual pv find the threshold above which the energy should be stored (first day)
    threshold = find_threshold(res_pv_val[0: 0 + int(23 / timestep)], bat_size_e_adj - LevelOfCharge[0])

    for i in range(1, Nsteps):  # Loop hours
        # Every 24 hours find the threshold for the next day (assuming next 24 hours)
        if i % int(24/timestep) == 0:
            threshold = find_threshold(res_pv_val[i:i + int(23 / timestep)],
                                       bat_size_e_adj - LevelOfCharge[i])

        # PV to grid
        if res_pv[i] * n_inv < threshold:  # If residual load is below threshold
            inv2grid[i] = res_pv[i] * n_inv  # Sell to grid what is not consumed
        else:  # If load is above threshold
            inv2grid[i] = threshold * n_inv  # Sell to grid what is below the threshold
            pv2store[i] = min(max(0, (res_pv[i] - threshold) * n_bat / n_inv),
                              (bat_size_e_adj - LevelOfCharge[i - 1]) / timestep )  # Store what is above the threshold and fits in battery
        pv2inv[i] = pv2inv[i] + inv2grid[i] / n_inv  # DC

        store2inv[i] = min(bat_size_p_adj,  # DC
                           res_load[i] / n_inv,
                           LevelOfCharge[i - 1] / timestep)

        LevelOfCharge[i] = min(LevelOfCharge[i - 1] - (store2inv[i] - pv2store[i] - grid2store[i]) * timestep,
                               bat_size_e_adj ) # DC

    inv2load = inv2load + store2inv * n_inv  # AC
    grid2load = demand - inv2load  # AC

    out = {'pv2inv': pv2inv,
            'res_pv': res_pv,
            'pv2store': pv2store,
            'inv2load': inv2load,
            'grid2load': grid2load,
            'store2inv': store2inv,
            'LevelOfCharge': LevelOfCharge,
            'inv2grid': inv2grid
            # 'grid2store': grid2store
            }
    if not return_series:
        out_pd = {}
        for k, v in out.items():  # Create dictionary of pandas series with same index as the input pv
            out_pd[k] = pd.Series(v, index=pv.index)
        out = out_pd
    return out



