
"""
Economics
"""

import os
import numpy as np
import pandas as pd
from prosumpy import base_sc,dispatch_max_sc,print_analysis
import datetime
import matplotlib.pyplot as plt

import numpy_financial as npf



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
    interest = EconomicVar['WACC'] # Discount rate, -
    net_metering = EconomicVar['net_metering']  # Boolean variable for the net metering scheme 
    years = EconomicVar['time_horizon'] # time horizon for the investment

    # Grid connection
    C_grid_fixed = EconomicVar['C_grid_fixed']  # Fixed grid tariff per year, €
    C_grid_kW    = EconomicVar['C_grid_kW']     # Fixed cost per installed grid capacity, €/kW 

    # Sell to the grid
    P_FtG      = EconomicVar['P_FtG']       # Purchase price of electricity fed to the grid, €/MWh  (price of energy sold to the grid)
    C_grid_FtG = 0.  # Grid fees for electricity fed to the grid, €/MWh      (cost to sell electricity to the grid)  
    C_TL_FtG   = 0.    # Tax and levies for electricity fed to the grid, €/MWh (cost to sell electricity to the grid)

    # Buy from the grid
    P_retail = ElPrices # array, it was EconomicVar['P_retail']

    # PV and batteries supports
    supportPV_INV  = 0.  # Investment support, % of investment
    supportPV_kW   = 0.  # Investment support proportional to the size, €/kW
    supportBat_INV = 0.  # to be added
    supportBat_kW  = 0.  # to be added

    # Self consumption
    P_support_SC = 0.    # Support to self-consumption, €/MWh                    (incentive to self consumption)  
    C_grid_SC    = 0.    # Grid fees for self-consumed electricity, €/MWh        (cost to do self consumption)
    C_TL_SC      = 0.    # Tax and levies for self-consumed electricity, €/MWh   (cost to do self consumption)
 
    
    # Initialize cash flows array 
    CashFlows = np.zeros(int(years)+1)    

    # PV investment, no replacements:
    PVInvestment = FixedPVCost + Inv['PVCost_kW'] * E['CapacityPV']
    
    # Battery investment with one replacement after the battery lifetime (10 years)
    BatteryInvestment  = (FixedBatteryCost + Inv['BatteryCost_kWh'] * E['CapacityBattery'])
 
    # Adding investment costs to cash flows array
    CashFlows[0]  = - PVInvestment - BatteryInvestment
    CashFlows[10] = - BatteryInvestment
    
    # O&M
    CashFlows[1:21] = CashFlows[1:21] - Inv['OM'] * (BatteryInvestment + PVInvestment)
    
    # Annual costs for grid connection
    Capacity = np.max(E['Load'])
    AnnualCostGrid = C_grid_fixed + C_grid_kW * Capacity
    
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
    
    
    # Reference case energy expenditure
    RefEnExpend = sum(E['Load']*ElPrices*timestep)
    
    CashFlows[1:21] = CashFlows[1:21] + Income_FtG + Income_SC - Cost_BtG - AnnualCostGrid + RefEnExpend
    CashFlowsAct = np.zeros(len(CashFlows))
    NPVcurve = np.zeros(len(CashFlows))

    for i in range(len(CashFlows)):
        CashFlowsAct[i] = CashFlows[i]/(1+interest)**(i)

    NPVcurve[0] = CashFlowsAct[0]

    for i in range(len(CashFlows)-1):
        NPVcurve[i+1] = NPVcurve[i]+CashFlowsAct[i+1]
        
    NPV = npf.npv(interest,CashFlows)
    out['NPV'] = NPV
       
    plt.plot(NPVcurve)
       
    zerocross = np.where(np.diff(np.sign(NPVcurve)))[0]
    if bool(zerocross):
        x1 = zerocross[0]
        x2 = zerocross[0]+1
        xs = [x1,x2]
        y1 = NPVcurve[zerocross[0]]
        y2 = NPVcurve[zerocross[0]+1]
        ys = [y1,y2]
        PBP = np.interp(0,ys,xs)
    else:
        PBP = 9999.
    
    out['PBP'] = PBP
    
    IRR = npf.irr(CashFlows)
    out['IRR'] = IRR

    # Annual electricity bill
    out['RevSelling'] = Income_FtG
    out['CostBuying'] = Cost_BtG
    out['AnnualGridCosts'] = AnnualCostGrid
    out['ElBill'] = Income_FtG - Cost_BtG - AnnualCostGrid # eur/y
       
    # LCOE equivalent, as if the grid was a generator
    NPV_Battery_reinvestment = (FixedBatteryCost + Inv['BatteryCost_kWh'] * E['CapacityBattery']) / (1+interest)**Inv['BatteryLifetime']
    BatteryInvestment += NPV_Battery_reinvestment
    CRF = interest * (1+interest)**Inv['PVLifetime']/((1+interest)**Inv['PVLifetime']-1)
    NetSystemCost = PVInvestment * (1 - supportPV_INV) - supportPV_kW * E['CapacityPV']  \
                    + BatteryInvestment * (1 - supportBat_INV) - supportBat_kW * E['CapacityBattery']
    AnnualInvestment = NetSystemCost * CRF + Inv['OM'] * (BatteryInvestment + PVInvestment)
    out['costpermwh'] = ((AnnualInvestment + AnnualCostGrid - Income_FtG - (P_support_SC - C_grid_SC - C_TL_SC)*sum(E['SC']*timestep)/1000 + Cost_BtG) / sum(E['Load']*timestep))*1000. #eur/MWh
    out['cost_grid'] = AnnualCostGrid/sum(E['Load']*timestep)*1000
    
    return out


def yearlyprices(scenario,timeslots,prices,stepperhour):

    stepperhour = int(stepperhour)    

    endday = datetime.datetime.strptime('1900-01-02 00:00:00',"%Y-%m-%d %H:%M:%S")

    HSdayhours = []
    HSdaytariffs = []
    CSdayhours = []
    CSdaytariffs = []
    
    for i in timeslots['HSday']:
        starthour = datetime.datetime.strptime(i[0],'%H:%M:%S')
        HSdayhours.append(starthour)
    
    for i in range(len(HSdayhours)):
        start = HSdayhours[i]
        end = HSdayhours[i+1] if i < len(HSdayhours)-1 else endday
        delta = end - start
        for j in range(stepperhour*int(delta.seconds/3600)):
            price = prices[scenario][timeslots['HSday'][i][1]]/1000.
            HSdaytariffs.append(price)
    
    for i in timeslots['CSday']:
        starthour = datetime.datetime.strptime(i[0],'%H:%M:%S')
        CSdayhours.append(starthour)
    
    for i in range(len(CSdayhours)):
        start = CSdayhours[i]
        end = CSdayhours[i+1] if i < len(CSdayhours)-1 else endday
        delta = end - start
        for j in range(stepperhour*int(delta.seconds/3600)):
            price = prices[scenario][timeslots['CSday'][i][1]]/1000.
            CSdaytariffs.append(price)
    
    startyear = datetime.datetime.strptime('2015-01-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    HSstart = datetime.datetime.strptime(timeslots['HSstart'],"%Y-%m-%d %H:%M:%S")
    CSstart = datetime.datetime.strptime(timeslots['CSstart'],"%Y-%m-%d %H:%M:%S")
    endyear = datetime.datetime.strptime('2016-01-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    
    ytariffs = []
    
    deltaCS1 = HSstart - startyear
    deltaHS  = CSstart - HSstart
    deltaCS2 = endyear - CSstart
    
    for i in range(deltaCS1.days):
        ytariffs.extend(CSdaytariffs)
    for i in range(deltaHS.days):
        ytariffs.extend(HSdaytariffs)
    for i in range(deltaCS2.days):
        ytariffs.extend(CSdaytariffs)
    
    out = np.asarray(ytariffs)
            
    return out




























