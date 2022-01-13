
import os
import numpy as np
import pandas as pd
import json
import time
import pickle
from functions import yearlyprices,mostrapcurve, run,strategy1


"""
Inputs:
    pv profile,
    pv capacity, 
    battery capacity, 
    price scenario, 
    technology costs, 
    economic variables,
    timestep,
    step per hour,
    demand

Functions:
    choose most rapresentative curve,
    models cases from excel
        prosumpy functions
        economic analysis functions
        load shifting functions
    
"""

inputs = {'CapacityPV': 0.,
          'CapacityBattery': 0.}

pvpeak = 0. #kW ##########rivedere
pvfile = r'.\autoconsommation\data\pv.pkl'
pvadim = pd.read_pickle(pvfile)
pv = pvadim * pvpeak # kW
pv = pv.iloc[:,0]
pv.values[:] = 0


name = '1f.pkl'
path = r'.\autoconsommation\data'
file = os.path.join(path,name)
demands = pd.read_pickle(file)
columns = ['StaticLoad','TumbleDryer','DishWasher','WashingMachine','DomesticHotWater','HeatPumpPower','EVCharging']
appshift = ['WashingMachine','TumbleDryer','DishWasher']

name = '1f_occ.pkl'
file = os.path.join(path,name)
occupancys = pd.read_pickle(file)

param_tech = {'BatteryCapacity':  0.,
              'BatteryEfficiency': 0.9,
              'MaxPower': 7.,
              'InverterEfficiency': 1.,
              'timestep': .25}

# Technology costs
Inv = {'FixedPVCost':0,
        'PVCost_kW':1500,
        'FixedBatteryCost':100,
        'BatteryCost_kWh':200,
        'PVLifetime':20,
        'BatteryLifetime':10,
        'OM':0.015} # eur/year/eur of capex (both for PV and battery)

with open(r'.\autoconsommation\economics\inputs_econ.json') as g:
  econ = json.load(g)

timeslots = econ['timeslots']
prices = econ['prices']
scenario = 'test'

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
index = mostrapcurve(pv,demands,param_tech,inputs,EconomicVar,Inv,ElPrices,timestep,columns)

test = run(pv,demands[index],param_tech,inputs,EconomicVar,Inv,ElPrices,timestep,columns,prices,scenario)


"""
Load shifting for the appliances
Strategy 1
"""

# Admissible time windows according to energy prices
with open(r'.\autoconsommation\economics\inputs_econ.json') as g:
  econ = json.load(g)

stepperhourshift=60
yprices = yearlyprices(scenario,timeslots,prices,stepperhourshift)
admprices = np.where(yprices <= prices[scenario]['hollow']/1000,1.,0.)
admprices = np.append(admprices,yprices[-1])

# Custom admissible windows
admcustom = np.ones(len(admprices))
for i in range(len(admprices)-60):
    if admprices[i]-admprices[i+60] == 1.:
        admcustom[i] = 0
               
# Adimissibile time windows according to occupancy

occ = np.zeros(len(occupancys[index][0]))
for i in range(len(occupancys[index])):
    occupancys[index][i] = [1 if a==1 else 0 for a in occupancys[index][i]]
    occ += occupancys[index][i]
    
occ = [1 if a >=1 else 0 for a in occ]    
occ = occ[:-1].copy()
occupancy = np.zeros(len(demands[index]['StaticLoad']))
for i in range(len(occ)):
    for j in range(10):
        occupancy[i*10+j] = occ[i]
occupancy[-1] = occupancy[-2]

# Resulting admissibile time windows
admtimewin = admprices*admcustom*occupancy

# Probability of load being shifted
probshift = 1.

startshift = time.time()

for app in appshift:
    print("---"+str(app)+"---")
    app_n,ncyc,ncycshift,maxshift,avgshift,cycnotshift = strategy1(demands[index][app],admtimewin,probshift)

    demands[index].insert(len(demands[index].columns),app+'Shift', app_n,True)
    
    conspre  = sum(demands[index][app])/60./1000.
    conspost = sum(demands[index][app+'Shift'])/60./1000.
    print("Original consumption: {:.2f}".format(conspre))
    print("Number of cycles: {:}".format(ncyc))
    print("Number of cycles shifted: {:}".format(ncycshift))
    print("Consumption after shifting (check): {:.2f}".format(conspost))
    print("Max shift: {:.2f} hours".format(maxshift))
    print("Avg shift: {:.2f} hours".format(avgshift))
    print("Unable to shift {:} cycles".format(cycnotshift))

execshift = (time.time() - startshift)
print("Time to shift the appliances: {:.1f} seconds".format(execshift))

result = demands[index]

path = r'.\autoconsommation\results'
if not os.path.exists(path):
    os.makedirs(path)
    
name = 'test.pkl'
file = os.path.join(path,name)
with open(file, 'wb') as b:
    pickle.dump(result,b)




