import ulmo
import datetime

my_country = 'CZ'
begin = '1980-01-01'
st = ulmo.ncdc.gsod.get_stations(country=my_country)
stat_one = st.keys()[2]
ts = ulmo.ncdc.gsod.get_data(stat_one, start=begin, end=datetime.date.today())
ints = ts[ts.keys()[0]]
my_dates = []
vals = []
for itm in ints:
    my_dates.append(itm['date'])
    sno = itm['snow_depth']
    if sno > 900:
        sno = None
    vals.append(sno)

import pandas as pd
df = pd.DataFrame(ints).set_index('date')
df.set_index(my_dates)
df[df.snow_depth > 900] = NaN

from pylab import *
plot(my_dates, vals)