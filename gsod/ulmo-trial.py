import ulmo
import datetime
import db_save

my_country = 'DE'
begin = '2010-01-01'
parameter = 'snow_depth'
save_stations = False

if save_stations:
    stations = ulmo.ncdc.gsod.get_stations()
    db_save.add_sites(stations)
else:
    stations = db_save.get_sites()

st0 = stations[0]
ts = ulmo.ncdc.gsod.get_data(st0['site_code'], start='2010-01-01', end=datetime.date.today(), parameters='snow_depth')
ts_dict = ts[ts.keys()[0]]

for st in stations:
    ts = ulmo.ncdc.gsod.get_data(st['site_code'], start='2010-01-01', end=datetime.date.today(), parameters='snow_depth')
    ts_list = ts[ts.keys()[0]]

    if ts_list:
        for val in ts_list:
            val['time'] = val.pop('date')
            if val['snow_depth'] > 900:
                val['snow_depth'] = -9999
            else:
                val['snow_depth'] = int(round(val['snow_depth'] * 2.54))
            val['val'] = val.pop('snow_depth')
            val['site_id'] = st['site_id']
            val['qualifier'] = 1

        db_save.add_values(ts_list)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


#make this into a pandas time series data frame
df = pd.DataFrame(ts_dict).set_index('date')
df.index = pd.DatetimeIndex(df.index)
df['snow_depth'][df.snow_depth > 900] = np.NaN

plt.figure()
df[['mean_temp','snow_depth']]['20091201':'20100331'].plot()