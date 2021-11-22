
"""
Economics
"""

import os
import numpy as np
import pandas as pd
from prosumpy import base_sc, print_analysis
import datetime




def EconomicAnalysis(E,EconomicVar,Inv,ElPrices,timestep):
    '''
    Calculation of the profits linked to the PV/battery installation, user perspective
       
    :param E: Output of the "EnergyFlows" function: dictionary of the computed yearly qunatities relative to the PV battery installation 
    :param EconomicVar: Dictionary with the financial variables of the considered country   
    :param Inv: Investment data. Defined as a dictionary with the fields 'FixedPVCost','PVCost_kW','FixedBatteryCost','BatteryCost_kWh','PVLifetime','BatteryLifetime','OM'
    :return: List comprising the Profitability Ratio and the system LCOE
    '''
    
    # Defining output dictionnary
    out = {}
    
    # Updating the fixed costs if PV or batteries capacities = 0
    if E['CapacityPV'] == 0:
        FixedPVCost = 0
    else:
        FixedPVCost = Inv['FixedPVCost']
        
    if E['CapacityBattery'] == 0:
        FixedBatteryCost = 0
    else:
        FixedBatteryCost = Inv['FixedBatteryCost']
     
    # Load economic data:

    # General
    i = EconomicVar['WACC'] # Discount rate, -
    net_metering = EconomicVar['net_metering']  # Boolean variable for the net metering scheme    

    # Grid connection
    C_grid_fixed = EconomicVar['C_grid_fixed']  # Fixed grid tariff per year, €
    C_grid_kW    = EconomicVar['C_grid_kW']     # Fixed cost per installed grid capacity, €/kW 

    # Sell to the grid
    P_FtG      = EconomicVar['P_FtG']       # Purchase price of electricity fed to the grid, €/MWh  (price of energy sold to the grid)
    C_grid_FtG = EconomicVar['C_grid_FtG']  # Grid fees for electricity fed to the grid, €/MWh      (cost to sell electricity to the grid)  
    C_TL_FtG   = EconomicVar['C_TL_FtG']    # Tax and levies for electricity fed to the grid, €/MWh (cost to sell electricity to the grid)

    # Buy from the grid
    P_retail = ElPrices # array, it was EconomicVar['P_retail']

    # PV and batteries supports
    supportPV_INV  = 0  # Investment support, % of investment
    supportPV_kW   = 0  # Investment support proportional to the size, €/kW
    supportBat_INV = 0  # to be added
    supportBat_kW  = 0  # to be added

    # Self consumption
    P_support_SC = 0    # Support to self-consumption, €/MWh                    (incentive to self consumption)  
    C_grid_SC    = 0    # Grid fees for self-consumed electricity, €/MWh        (cost to do self consumption)
    C_TL_SC      = 0    # Tax and levies for self-consumed electricity, €/MWh   (cost to do self consumption)
    
    
    # Battery investment with one replacement after the battery lifetime (10 years)
    NPV_Battery_reinvestment = (FixedBatteryCost + Inv['BatteryCost_kWh'] * E['CapacityBattery']) / (1+i)**Inv['BatteryLifetime']
    BatteryInvestment = (FixedBatteryCost + Inv['BatteryCost_kWh'] * E['CapacityBattery']) + NPV_Battery_reinvestment
    
    # PV investment, no replacements:
    PVInvestment = FixedPVCost + Inv['PVCost_kW'] * E['CapacityPV']
    
    # Investment costs:
    NetSystemCost = PVInvestment * (1 - supportPV_INV) - supportPV_kW * E['CapacityPV']  \
                    + BatteryInvestment * (1 - supportBat_INV) - supportBat_kW * E['CapacityBattery']
    
    # Capital Recovery Factor, %
    CRF = i * (1+i)**Inv['PVLifetime']/((1+i)**Inv['PVLifetime']-1)
    
    # Annual investment
    AnnualInvestment = NetSystemCost * CRF + Inv['OM'] * (BatteryInvestment + PVInvestment)
    
    # Total investment without the subsidies (O&M could also possibly be removed...):
    ReferenceAnnualInvestment = (BatteryInvestment + PVInvestment) * (CRF  + Inv['OM'])
    ReferenceAnnualInvestment = np.maximum(1e-7,ReferenceAnnualInvestment) # avoids division by zero
    
    # Annual costs for grid connection
    AnnualCost = C_grid_fixed + C_grid_kW * E['CapacityPV']
    
    # Energy expenditure and revenues
    # Both in case of net metering or not
    
    if net_metering:
        # Revenues selling to the grid
        # Fixed selling price and cost
        Income_FtG = np.maximum(0,sum(E['ACGeneration']-E['Load'])*timestep) * (P_FtG - C_grid_FtG - C_TL_FtG)/1000
        Income_SC = 0
        """
        Old equations:
        Income_FtG = np.maximum(0,E['ACGeneration']-E['Load']) * (P_FtG - C_grid_FtG - C_TL_FtG)/1000
        Income_SC = (P_support_SC + P_retail - C_grid_SC - C_TL_SC) * np.minimum(E['ACGeneration'],E['Load'])/1000  # the retail price on the self-consumed part is included here since it can be considered as a support to SC    
        """
        # Expenditures buying from the grid
        Cost_BtG = np.maximum(sum(P_retail*(E['Load']-E['ACGeneration'])*timestep),0)      
    else:
        # Revenues selling to the grid
        # Fixed selling price and cost

        Income_FtG = sum(E['ToGrid']*timestep) * (P_FtG - C_grid_FtG - C_TL_FtG)/1000
        Income_SC = 0
        """
        Old equations:
        Income_FtG = E['ToGrid'] * (P_FtG - C_grid_FtG - C_TL_FtG)/1000
        Income_SC = (P_support_SC + P_retail - C_grid_SC - C_TL_SC) * E['SC']/1000  # the retail price on the self-consumed part is included here since it can be considered as a support to SC
        """
        # Expenditures buying from the grid
        Cost_BtG = sum(P_retail * E['FromGrid']*timestep)

    # Profitability Ratio
    

    
    Profit =  Income_FtG + Income_SC - AnnualInvestment - AnnualCost
    out['PR'] = Profit/ReferenceAnnualInvestment*100
    
    # print(Profit)
    # print(ReferenceAnnualInvestment)
    # print(AnnualInvestment)
    # print(AnnualCost)
    # print(Income_FtG)
    print(sum(E['SC']*timestep))
    # print(Cost_BtG)
    print(sum(E['Load']*timestep))

    
    # LCOE as if the grid was a generator
    out['LCOE'] = (AnnualInvestment + AnnualCost - Income_FtG - (P_support_SC - C_grid_SC - C_TL_SC) * sum(E['SC']*timestep)/1000 + Cost_BtG)/sum(E['Load']*timestep)
    
    # LCOE of storage
    if sum(E['FromBattery']) > 1:
        out['LCOE_stor'] = BatteryInvestment * ( CRF + Inv['OM']) / sum(E['FromBattery']*timestep)
    else:
        out['LCOE_stor'] = np.nan

    return out



def electricityprices(prices):

    sts1 = datetime.datetime.strptime(prices['STS1'],'%H:%M:%S')
    sts2 = datetime.datetime.strptime(prices['STS2'],'%H:%M:%S')
    sts3 = datetime.datetime.strptime(prices['STS3'],'%H:%M:%S')
    sts4 = datetime.datetime.strptime(prices['STS4'],'%H:%M:%S')
    wts1 = datetime.datetime.strptime(prices['WTS1'],'%H:%M:%S')
    wts2 = datetime.datetime.strptime(prices['WTS2'],'%H:%M:%S')
    wts3 = datetime.datetime.strptime(prices['WTS3'],'%H:%M:%S')
    endday = datetime.datetime.strptime('1900-01-02 00:00:00',"%Y-%m-%d %H:%M:%S")
    
    summerday = []
    
    sd1 = sts2 - sts1
    sd2 = sts3 - sts2
    sd3 = sts4 - sts3
    sd4 = endday - sts4
    
    for i in range(4*int(sd1.seconds/3600)):
        summerday.append(prices['priceSTS1'])
    for i in range(4*int(sd2.seconds/3600)):
        summerday.append(prices['priceSTS2'])
    for i in range(4*int(sd3.seconds/3600)):
        summerday.append(prices['priceSTS3'])
    for i in range(4*int(sd4.seconds/3600)):
        summerday.append(prices['priceSTS4'])
        
    winterday = []
    
    wd1 = wts2 - wts1
    wd2 = wts3 - wts2
    wd3 = endday - wts3
    
    for i in range(4*int(wd1.seconds/3600)):
        winterday.append(prices['priceWTS1'])
    for i in range(4*int(wd2.seconds/3600)):
        winterday.append(prices['priceWTS2'])
    for i in range(4*int(wd3.seconds/3600)):
        winterday.append(prices['priceWTS3'])
    
    
    startyear = datetime.datetime.strptime('2015-01-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    summerstart = datetime.datetime.strptime(prices['summerstart'],"%Y-%m-%d %H:%M:%S")
    summerend = datetime.datetime.strptime(prices['summerend'],"%Y-%m-%d %H:%M:%S")
    endyear = datetime.datetime.strptime('2016-01-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    
    diff1 = summerstart - startyear
    diff2 = summerend - summerstart
    diff3 = endyear - summerend
    
    year = []
    
    for i in range(diff1.days):
        year.extend(winterday)
    for i in range(diff2.days):
        year.extend(summerday)
    for i in range(diff3.days):
        year.extend(winterday)
        
    out = np.asarray(year)
    
    return out





# First inputs required 
inputs = {'CapacityPV': 10.,
          'CapacityBattery': 0.,}

# Loading PV data
pvpeak = inputs['CapacityPV'] #kW
pvfile = r'.\tests\data\pv.pkl'
pvadim = pd.read_pickle(pvfile)
pv = pvadim * pvpeak # kW
pv = pv.iloc[:,0]

# Loading demand data
ncase = 1
nrun = 1
pathtofolder = r'.\tests\data\demand\case_{0}'.format(ncase)
runname = 'run_{0}'.format(nrun)
filename = runname+'.pkl'
path = os.path.join(pathtofolder,filename)
demand = pd.read_pickle(path) # W
demand = demand/1000. #kW
demand = demand.iloc[:,0]

# Launching prosumpy
param_tech = {'BatteryCapacity': inputs['CapacityBattery'],
              'BatteryEfficiency': 0.,
              'InverterEfficiency': 1.,
              'timestep': .25,
              'MaxPower': 0.}

outputs = base_sc(pv, demand, return_series=False)
print_analysis(pv, demand, param_tech, outputs)

# Updating inputs for economic analysis with results from prosumpy
inputs['ACGeneration'] = pv # should be equal to outputs['inv2grid']+outputs['inv2load']
inputs['Load'] = demand
inputs['ToGrid'] = outputs['inv2grid']
inputs['FromGrid'] = outputs['grid2load']
inputs['SC'] = outputs['inv2load']
inputs['FromBattery'] = outputs['store2inv']

# Technology costs
Inv = {'FixedPVCost':0,
        'PVCost_kW':1500,
        'FixedBatteryCost':300,
        'BatteryCost_kWh':200,
        'PVLifetime':20,
        'BatteryLifetime':10,
        'OM':0.015} # eur/year/eur of capex (both for PV and battery)

# Economic parameteres
EconomicVar = {'WACC': 0.05,
                'net_metering': False,
                'C_grid_fixed':0.,
                'C_grid_kW':0.,
                'P_FtG': 40.,
                'C_grid_FtG': 0.,
                'C_TL_FtG':0.}

# Defining array with electrcity prices
prices = {'summerstart': "2015-04-01 00:00:00",
          'summerend': "2015-09-01 00:00:00",
          'STS1':'00:00:00',
          'STS2':'06:00:00',
          'STS3':'17:00:00',
          'STS4':'21:00:00',
          'WTS1':'00:00:00',
          'WTS2':'06:00:00',
          'WTS3':'17:00:00',
          'priceSTS1': 0.10,
          'priceSTS2': 0.20,
          'priceSTS3': 0.25,
          'priceSTS4': 0.15,
          'priceWTS1': 0.10,
          'priceWTS2': 0.20,
          'priceWTS3': 0.18}

ElPrices = electricityprices(prices)

# Launching economic analysis
timestep = 0.25 # hrs
results = EconomicAnalysis(inputs,EconomicVar,Inv,ElPrices,timestep)

























