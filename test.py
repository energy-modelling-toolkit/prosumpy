import os
import pandas as pd
from prosumpy import base_sc, print_analysis



# demand = pd.read_csv(r'./tests/data/demand_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv_1kW = pd.read_csv(r'./tests/data/pv_example.csv', index_col=0, header=None, parse_dates=True, squeeze=True)
# pv = pv_1kW*10.

# PV
pvpeak = 10. #kW
pvfile = r'.\tests\data\pv.pkl'
pvadim = pd.read_pickle(pvfile)
pv = pvadim * pvpeak # kW
pv = pv.iloc[:,0]

# Demand
ncase = 1
nrun = 1
pathtofolder = r'.\tests\data\demand\case_{0}'.format(ncase)
runname = 'run_{0}'.format(nrun)
filename = runname+'.pkl'
path = os.path.join(pathtofolder,filename)
demand = pd.read_pickle(path) # W
demand = demand/1000. #kW
demand = demand.iloc[:,0]


# Parameters required by prosumpy
param_tech = {'BatteryCapacity': 0.,
              'BatteryEfficiency': 0.,
              'InverterEfficiency': 1.,
              'timestep': .25,
              'MaxPower': 0.}


outputs = base_sc(pv, demand, return_series=False)
print_analysis(pv, demand, param_tech, outputs)






















