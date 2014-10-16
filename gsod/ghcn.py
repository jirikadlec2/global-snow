import ulmo
import datetime

my_country = 'US'
begin = '2010-01-01'
parameter = 'snow_depth'
save_stations = False

#get all the stations
all_st = ulmo.ncdc.ghcn_daily.get_stations()

for st_code in all_st:
    st_obj = all_st[st_code]
    sno_data = ulmo.ncdc.ghcn_daily.get_data(st_code, elements='SNWD', update=False, as_dataframe=True)
    if (len(sno_data) > 0):
        break
        #save or update station
        #save or update data values

sno_data['SNWD']['1950':'2014'].plot()


st = ulmo.ncdc.ghcn_daily.get_stations(country='EZ', as_dataframe=True)

data = ulmo.ncdc.ghcn_daily.get_data('USC00427064', elements='SNWD', update=False, as_dataframe=True)

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