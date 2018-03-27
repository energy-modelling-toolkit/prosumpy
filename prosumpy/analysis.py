"""This module contains functions to analyze the results of the dispatch algorithm"""

import numpy as np

def print_analysis(pv, demand, param, E):
    """ Print statistics and information of the dispatched solution

    Arguments
        pv (pd.Series): PV timeseries
        demand (pd.Series): demand timeseries
        param (dict): dictionary of technical parameters
        E (dict): dictionary of energy flows as estimated by the algorithm
    Returns
        none

    """
    timestep = param['timestep']
    SelfConsumption = np.sum(E['inv2load']) * timestep
    TotalFromGrid = np.sum(E['grid2load']) * timestep
    TotalToGrid = np.sum(E['inv2grid']) * timestep
    TotalLoad = demand.sum() * timestep
    TotalPV = pv.sum() * timestep
    TotalBatteryGeneration = np.sum(E['store2inv']) * timestep
    TotalBatteryConsumption = np.sum(E['pv2store']) * timestep
    BatteryLosses = TotalBatteryConsumption - TotalBatteryGeneration
    InverterLosses = (TotalPV - BatteryLosses) * (1 - param['InverterEfficiency'])
    SelfConsumptionRate = SelfConsumption / TotalPV * 100             # in %
    SelfSufficiencyRate = SelfConsumption / TotalLoad * 100
    AverageDepth = TotalBatteryGeneration / (365 * param['BatteryCapacity'])
    Nfullcycles = 365 * AverageDepth
    residue = TotalPV + TotalFromGrid - TotalToGrid - BatteryLosses - InverterLosses - TotalLoad

    print ('Total yearly consumption: {:.3g} kWh'.format(TotalLoad))
    print ('Total PV production: {:.3g} kWh'.format(TotalPV))
    print ('Self Consumption: {:.3g} kWh'.format(SelfConsumption))
    print ('Total fed to the grid: {:.3g} kWh'.format(TotalToGrid))
    print ('Total bought from the grid: {:.3g} kWh'.format(TotalFromGrid))
    print ('Self consumption rate (SCR): {:.3g}%'.format(SelfConsumptionRate))
    print ('Self sufficiency rate (SSR): {:.3g}%'.format(SelfSufficiencyRate))
    print ('Amount of energy provided by the battery: {:.3g} kWh'.format(TotalBatteryGeneration))
    print ('Average Charging/Discharging depth: {:.3g}'.format(AverageDepth))
    print ('Number of equivalent full cycles per year: {:.3g} '.format(Nfullcycles))
    print ('Total battery losses: {:.3g} kWh'.format(BatteryLosses))
    print ('Total inverter losses: {:.3g} kWh'.format(InverterLosses))
    print ('Residue (check): {:.3g} kWh'.format(residue))
