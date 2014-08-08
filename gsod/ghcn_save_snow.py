import ulmo
import db_save

#get all the stations
all_st = ulmo.ncdc.ghcn_daily.get_stations()

for st_code in all_st:
    st_obj = all_st[st_code]
    print st_obj
    sno_data = ulmo.ncdc.ghcn_daily.get_data(st_code, elements='SNWD', update=False, as_dataframe=True)
    if (len(sno_data) > 0):
        
        ts_list2 = []
        sno = sno_data['SNWD']
        sno2 = sno['value'].dropna()
        
        #now get the site id and save site if required
        site_from_db = db_save.get_site_id(st_code)
        if site_from_db == None:
            site_id = db_save.add_site(st_code, st_obj)
        else:
            site_id = site_from_db[0]
        #check for NaN!
        for dat, val in sno2.iteritems():
            dat2 = dat.start_time.strftime('%Y-%m-%d')
            val2 = {'time': dat2, 'site_id': site_id, 'qualifier': 1, 'val': round(val/10)}
            ts_list2.append(val2)

        if len(ts_list2) > 0:
            db_save.add_values(ts_list2)     
