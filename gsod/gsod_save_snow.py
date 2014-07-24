
import datetime
import db_save
import my_gsod

year = 1928
parameter = 'snow_depth'
save_stations = False
save_nodata = False

if save_stations:
    import ulmo
    stations = ulmo.ncdc.gsod.get_stations()
    db_save.add_sites(stations)
else:
    stations = db_save.get_sites()

sites_saved = 0
sites_checked = 0
sites_error = 0
year = 2014
for st in stations:
    try:
        ts_list = my_gsod.get_data(st['site_code'], year)

        if ts_list:
            ts_list2 = []
            for val in ts_list:
                if val['snow_depth'] > 900:
                    if save_nodata:
                        sno_cm = -9999
                        ts_list2.append({'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm })
                else:
                    sno_cm = int(round(val['snow_depth'] * 2.54))
                    val2 = {'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm }
                    ts_list2.append(val2)

            if len(ts_list2) > 0:
                db_save.add_values(ts_list2)
                sites_saved += 1
        sites_checked += 1
    except:
        sites_error += 1


def save_gsod_snow_year(stations, year):
    sites_saved = 0
    sites_checked = 0
    sites_error = 0
    for st in stations:
    try:
        ts_list = my_gsod.get_data(st['site_code'], year)

        if ts_list:
            ts_list2 = []
            for val in ts_list:
                if val['snow_depth'] > 900:
                    if save_nodata:
                        sno_cm = -9999
                        ts_list2.append({'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm })
                else:
                    sno_cm = int(round(val['snow_depth'] * 2.54))
                    val2 = {'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm }
                    ts_list2.append(val2)

            if len(ts_list2) > 0:
                db_save.add_values(ts_list2)
                sites_saved += 1
        sites_checked += 1
    except:
        sites_error += 1

    return {'saved': sites_saved, 'checked': sites_checked, 'error': sites_error}