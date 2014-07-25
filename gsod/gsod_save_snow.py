import datetime
import findtools
import db_save
import my_gsod
import ulmo

DB_CONNECTION = 'mysql+pymysql://root:@127.0.0.1/snow'
NCDC_GSOD_DIR = '/home/keskari/gsod_data'

def get_stations_from_year(year, gsod_dir, db):
    txt_files_pattern = findtools.Match(filetype='f', name='*' + year + '.txt')
    found_files = findtools.find_files(path=gsod_dir, match=txt_files_pattern)
    for f in found_files:
        print(f)
    db_save.DB_CONNECTION = db
    db_files = db_save.get_sites()

def save_gsod_snow_year(stations, year, db, save_nodata=False):
    db_save.DB_CONNECTION = db
    my_gsod.NCDC_GSOD_DIR = NCDC_GSOD_DIR
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
                            ts_list2.append(
                                {'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm})
                    else:
                        sno_cm = int(round(val['snow_depth'] * 2.54))
                        val2 = {'time': val['date'], 'site_id': st['site_id'], 'qualifier': 1, 'val': sno_cm}
                        ts_list2.append(val2)

                if len(ts_list2) > 0:
                    db_save.add_values(ts_list2)
                    sites_saved += 1
            sites_checked += 1
        except:
            sites_error += 1

    return {'saved': sites_saved, 'checked': sites_checked, 'error': sites_error}


def get_stations():
    st = db_save.get_sites()
    if not st:
        st = ulmo.ncdc.gsod.get_stations()
        db_save.add_sites(st)
        return db_save.get_sites()
    else:
        return st


if __name__ == "__main__":
    db_save.DB_CONNECTION = DB_CONNECTION
    stations = get_stations()
    for year in range(2013,1929,-1):
        save_gsod_snow_year(stations, year)
        print(year)