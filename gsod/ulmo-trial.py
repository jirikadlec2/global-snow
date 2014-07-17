import ulmo
import datetime

my_country = 'CZ'
begin = '1980-01-01'
parameter = 'snow_depth'
st = ulmo.ncdc.gsod.get_stations(country=my_country)
stat_one = st.keys()[0]
ts = ulmo.ncdc.gsod.get_data(stat_one, start=begin, end=datetime.date.today())
ints = ts[ts.keys()[0]]

import pandas as pd
import numpy as np

df = pd.DataFrame(ints).set_index('date')

#make this into a true time series
df.index = pd.DatetimeIndex(df.index)
df[df.snow_depth > 900] = np.NaN
df[['mean_temp','snow_depth']]['20120101':'20131231'].plot()
