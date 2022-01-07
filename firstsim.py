
"""
Economics
"""

import os
import pandas as pd
from prosumpy import dispatch_max_sc,print_analysis
import json
from statistics import mean
from economics import EconomicAnalysis,yearlyprices
import numpy as np


"""
PV data
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
pv.values[:] = 0


"""
Economics inputs
"""

with open('economics/inputs_econ.json') as g:
  econ = json.load(g)

timeslots = econ['timeslots']
prices = econ['prices']
scenario = 'test'
        
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
stepperhour = 4
ElPrices = yearlyprices(scenario,timeslots,prices,stepperhour)

heel = np.where(ElPrices == prices[scenario]['heel']/1000,1.,0.)
hollow = np.where(ElPrices == prices[scenario]['hollow']/1000,1.,0.)
full =  np.where(ElPrices == prices[scenario]['full']/1000,1.,0.)
peak =  np.where(ElPrices == prices[scenario]['peak']/1000,1.,0.)


"""
Demand data
"""

# Loading demand data

path = r'.\firstsim'
names = ['1f_machine0','2f_machine0','4f_machine0']


mostrapcurve = []

for ii in range(3):

    name = names[ii]+'.pkl'
    file = os.path.join(path,name)
    demand_tot = pd.read_pickle(file) # W

    results = []
    
    for jj in range(10):
    
        demand = demand_tot[jj]
        demand = demand.sum(axis=1)
        demand = demand/1000. #kW
        # Resampling at 15 min
        demand = demand.to_frame()
        demand = demand.resample('15Min').mean()
        # Extracting ref year used in the simulation
        demand.index = pd.to_datetime(demand.index)
        year = demand.index.year[0]
        # Remove last row if is from next year
        nye = pd.Timestamp(str(year+1)+'-01-01 00:00:00')
        demand = demand.drop(nye)
        demand = demand.iloc[:,0]

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
        
        out = EconomicAnalysis(inputs,EconomicVar,Inv,ElPrices,timestep)
        results.append(out['ElBill'])
        
    meanelbill = mean(results)
    var = results-meanelbill
    index_min = min(range(len(var)), key=var.__getitem__)
    mostrapcurve.append(index_min+1)


#############################
#############################
#############################

res_mostrap = []

for kk in range (3):
    
    name = names[kk]+'.pkl'
    file = os.path.join(path,name)
    demand_tot = pd.read_pickle(file) # W

    demand = demand_tot[mostrapcurve[kk]]

    demand = demand.sum(axis=1)
    demand = demand/1000. #kW
    # Resampling at 15 min
    demand = demand.to_frame()
    demand = demand.resample('15Min').mean()
    # Extracting ref year used in the simulation
    demand.index = pd.to_datetime(demand.index)
    year = demand.index.year[0]
    # Remove last row if is from next year
    nye = pd.Timestamp(str(year+1)+'-01-01 00:00:00')
    demand = demand.drop(nye)
    demand = demand.iloc[:,0]

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
       
    out = EconomicAnalysis(inputs,EconomicVar,Inv,ElPrices,timestep)
    res = {}
    res['elbill'] = out['ElBill']
    
    res['heel'] = sum(demand*heel)/4
    res['hollow'] = sum(demand*hollow)/4
    res['full'] = sum(demand*full)/4
    res['peak'] = sum(demand*peak)/4
    
    res['peakdemand'] = np.max(demand)
    
    res_mostrap.append(res)

    
    
    


#############################
#############################
#############################


res_shifted = []

for ll in range (3):
    
    name = names[ll]+'_shifted.pkl'
    file = os.path.join(path,name)
    demand = pd.read_pickle(file) # W
    
    demand = demand.sum(axis=1)
    demand = demand/1000. #kW
    # Resampling at 15 min
    demand = demand.to_frame()
    demand = demand.resample('15Min').mean()
    # Extracting ref year used in the simulation
    demand.index = pd.to_datetime(demand.index)
    year = demand.index.year[0]
    # Remove last row if is from next year
    nye = pd.Timestamp(str(year+1)+'-01-01 00:00:00')
    demand = demand.drop(nye)
    demand = demand.iloc[:,0]

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
       
    out = EconomicAnalysis(inputs,EconomicVar,Inv,ElPrices,timestep)
    
    res = {}
    res['elbill'] = out['ElBill']
    
    res['heel'] = sum(demand*heel)/4
    res['hollow'] = sum(demand*hollow)/4
    res['full'] = sum(demand*full)/4
    res['peak'] = sum(demand*peak)/4
    
    res['peakdemand'] = np.max(demand)
    
    res_shifted.append(res)


