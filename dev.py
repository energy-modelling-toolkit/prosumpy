
"""
Economics
"""

import os
import pandas as pd
from prosumpy import base_sc,dispatch_max_sc,print_analysis
import json

from economics import EconomicAnalysis,yearlyprices


"""
PV and demand inputs
"""

# First inputs required 
inputs = {'CapacityPV': 0.,
          'CapacityBattery': 0.}

# Loading PV data
pvpeak = inputs['CapacityPV'] #kW
pvfile = r'.\tests\data\pv.pkl'
pvadim = pd.read_pickle(pvfile)
pv = pvadim * pvpeak # kW
pv = pv.iloc[:,0]


# Loading demand data
# ncase = 1
# nrun = 1
# pathtofolder = r'.\tests\data\demand\case_{0}'.format(ncase)
# runname = 'run_{0}'.format(nrun)
# filename = runname+'.pkl'
# path = os.path.join(pathtofolder,filename)

name = ['run_noshift.pkl','run_shift.pkl']
res = []

for j in range(2):
    demand = pd.read_pickle(name[j]) # W
    demand = demand/1000. #kW
    demand = demand.iloc[:,0]

    """
    Economics inputs
    """
    
    with open('economics/inputs_econ.json') as g:
      econ = json.load(g)
    
    timeslots = econ['timeslots']
    prices = econ['prices']
    scenario = 'test'
    
    
    """
    Basic self-consumption
    """
    # param_tech = {'BatteryCapacity':  inputs['CapacityBattery'],
    #               'BatteryEfficiency': 1.,
    #               'MaxPower': 0.,
    #               'InverterEfficiency': 1.,
    #               'timestep': .25}
    
    # outputs = base_sc(pv, demand, return_series=False)
    # print_analysis(pv, demand, param_tech, outputs)
    
    """
    PV + battery
    """
    param_tech = {'BatteryCapacity':  inputs['CapacityBattery'],
                  'BatteryEfficiency': 0.9,
                  'MaxPower': 7.,
                  'InverterEfficiency': 1.,
                  'timestep': .25}
    
    outputs = dispatch_max_sc(pv,demand,param_tech,return_series=False)
    print_analysis(pv, demand, param_tech, outputs)
    
    """
    Economic analysis
    """
    
    # Updating inputs for economic analysis with results from prosumpy
    inputs['ACGeneration'] = pv.to_numpy() # should be equal to outputs['inv2grid']+outputs['inv2load']
    inputs['Load'] = demand.to_numpy()
    inputs['ToGrid'] = outputs['inv2grid']
    inputs['FromGrid'] = outputs['grid2load']
    inputs['SC'] = outputs['inv2load']
    inputs['FromBattery'] = outputs['store2inv']
    
    
    # Technology costs
    Inv = {'FixedPVCost':0,
            'PVCost_kW':1500,
            'FixedBatteryCost':100,
            'BatteryCost_kWh':200,
            'PVLifetime':20,
            'BatteryLifetime':10,
            'OM':0.015} # eur/year/eur of capex (both for PV and battery)
    
    
    # Economic parameteres
    EconomicVar = {'WACC': 0.05, # weighted average cost of capital
                   'net_metering': False, # type of tarification scheme
                   'time_horizon': 20,
                   'C_grid_fixed':prices[scenario]['fixed'], # € annual fixed grid costs
                   'C_grid_kW': prices[scenario]['capacity'], # €/kW annual grid cost per kW 
                   'P_FtG': 40.}     # €/MWh electricity price to sell to the grid
    
    
    timestep = 0.25 # hrs
    ElPrices = yearlyprices(scenario,timeslots,prices)
    
    
    results = EconomicAnalysis(inputs,EconomicVar,Inv,ElPrices,timestep)
    res.append(results)
    




























