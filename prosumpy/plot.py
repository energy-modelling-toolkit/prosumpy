"""Plotting functions"""
import matplotlib.pyplot as plt

def plot_dispatch(pv, demand, E, week=30):
    """ Visualize dispatch algorithm for a specific week
    Parameters:
        demand (pd.Series): demand production
        pv (pd.Series): pv production
        E (dict):  Energy flows. Dictionary of pd.Series: res_pv, grid2load, store2inv, LevelOfCharge
    """

    sliced_index = (pv.index.week==week)
    pv_sliced = pv[sliced_index]
    demand_sliced = demand[sliced_index]
    self_consumption = E['inv2load'][sliced_index]
    res_pv_sliced = E['res_pv'][sliced_index]
    grid2load_sliced = E['grid2load'][sliced_index]
    store2inv_sliced = E['store2inv'][sliced_index]
    LevelOfCharge = E['LevelOfCharge'][sliced_index]
    inv2grid = E['inv2grid'][sliced_index]
    grid2load = E['grid2load'][sliced_index]



    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(17, 4*3), frameon=False,
                             gridspec_kw={'height_ratios': [3, 1, 1], 'hspace': 0.04})

    #fig, ax = plt.subplots(figsize=(17, 4))
    axes[0].plot(demand_sliced.index, demand_sliced, color='black', lw=2)
    axes[0].fill_between(self_consumption.index, 0, self_consumption, color='orange', alpha=.2)
    axes[0].fill_between(res_pv_sliced.index, self_consumption, pv_sliced , color='yellow', alpha=.2)
    axes[0].fill_between(store2inv_sliced.index,
                    pv_sliced,
                    store2inv_sliced + pv_sliced, color='blue',alpha=.2, hatch='//')
    axes[0].fill_between(grid2load_sliced.index,
                    pv_sliced + store2inv_sliced,
                    grid2load_sliced + pv_sliced + store2inv_sliced, color='grey', alpha=.2)
    axes[0].plot(grid2load_sliced.index, grid2load_sliced, color='red', ls=":", lw=1)
    axes[0].set_ylim([0, axes[0].get_ylim()[1] ])
    axes[0].set_ylabel('Power (kW)')

    axes[1].fill_between(LevelOfCharge.index, 0, LevelOfCharge, color='grey', alpha=.2)
    axes[1].set_ylabel('State of Charge (kWh)')

    axes[2].fill_between(inv2grid.index, 0, inv2grid, color='green', alpha=.2)
    axes[2].fill_between(inv2grid.index, 0, -grid2load, color='red', alpha=.2)
    axes[2].set_ylabel('In/out from grid (kWh)')

    return

