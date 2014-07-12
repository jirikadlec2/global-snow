import ulmo

st = ulmo.ncdc.gsod.get_stations(country='CZ')
stat_one = st.keys()[2]
ts = ulmo.ncdc.gsod.get_data(stat_one, start='2010-01-01', end='2014-06-30')
ints = ts[ts.keys()[0]]
my_dates = []
vals = []
for itm in ints:
    my_dates.append(itm['date'])
    sno = itm['snow_depth']
    if sno > 900:
        sno = None
    vals.append(sno)

from pylab import *
plot(my_dates, vals)