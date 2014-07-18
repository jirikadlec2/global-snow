import ulmo
import datetime
import db_save

begin = '1900-01-01'
parameter = 'snow_depth'
save_stations = False
save_nodata = False

if save_stations:
    stations = ulmo.ncdc.gsod.get_stations()
    db_save.add_sites(stations)
else:
    stations = db_save.get_sites()

for st in stations:
    ts = ulmo.ncdc.gsod.get_data(st['site_code'], parameters='snow_depth')
    ts_list = ts[ts.keys()[0]]

    ts_list2 = []
    if ts_list:
        for val in ts_list:
            val['time'] = val.pop('date')
            val['val'] = val.pop('snow_depth')
            val['site_id'] = st['site_id']
            val['qualifier'] = 1

            if val['val'] > 900:
                val['val'] = -9999
            else:
                val['val'] = int(round(val['val'] * 2.54))
                ts_list2.append(val)
        if save_nodata:
            db_save.add_values(ts_list)
        else:
            db_save.add_values(ts_list2)