import ulmo
import datetime

my_country = 'US'
begin = '2010-01-01'
parameter = 'snow_depth'
save_stations = False

st = ulmo.ncdc.ghcn_daily.get_stations(country='EZ', as_dataframe=True)

data = ulmo.ncdc.ghcn_daily.get_data('USC00427064', as_dataframe=True)

data_mile = ulmo.ncdc.ghcn_daily.get_data('EZ000011464', as_dataframe=True)
data_mile['SNWD']['2005':'2014'].plot()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


#make this into a pandas time series data frame
df = pd.DataFrame(ts_dict).set_index('date')
df.index = pd.DatetimeIndex(df.index)
df['snow_depth'][df.snow_depth > 900] = np.NaN

plt.figure()
df[['mean_temp','snow_depth']]['20091201':'20100331'].plot()