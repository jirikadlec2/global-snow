import math
import ulmo
import db_save

DB_CONNECTION = 'mysql+pymysql://root:@127.0.0.1/snow'
#DB_CONNECTION = 'postgresql+psycopg2://snow:snow@127.0.0.1/snow'
SITE_ID_SKIP = 30000
SITE_ID_MAX = 40000


def save_snow_utah():
    #get the utah stations
    utah_st = ulmo.ncdc.ghcn_daily.get_stations(country='US', state='UT', elements='SNWD', start_year=2014, end_year=2014, as_dataframe=False)


def save_snow_station(st_code):
    sno_data = ulmo.ncdc.ghcn_daily.get_data(st_code, elements='SNWD', update=False, as_dataframe=False)
    
    #now get the site id and save site if required
    site_from_db = db_save.get_site_id(st_code)
    if site_from_db == None:
        site_id = db_save.add_site(st_code, st_obj, 1)
    else:
        site_id = site_from_db[0]
    print site_id

    
def add_snow_variable():
    v = {'VariableCode':'SNWD',
        'VariableName':'Snow depth',
        'Speciation':'Not Applicable',
        'VariableunitsID':47,
        'SampleMedium':'Snow',
        'ValueType':'Field Observation',
        'IsRegular':True,
        'TimeSupport':1,
        'TimeunitsID':104,
        'DataType':'Average',
        'GeneralCategory':'Climate',
        'NoDataValue':-9999
        }
    return db_save.add_odm_object(v, 'variables', 'VariableID', 'VariableCode')


def add_snow_source():
    s = {'Organization':'WMO',
         'SourceDescription':'NCDC Daily Data',
         'SourceLink':'http://www1.ncdc.noaa.gov/pub/data/ghcn/daily/readme.txt',
         'ContactName':'ncdc.ghcnd@noaa.gov',
         'Phone':'1-385-204-2998',
         'Email':'ncdc.ghcnd@noaa.gov',
         'Address': 'Unknown',
         'City': 'Unknown',
         'State': 'Unknown',
         'ZipCode':'Unknown', 
         'Citation': 'GHCN: Global Historical Climatology Network Daily Data',
         'MetadataID': 1
         }
    return db_save.add_odm_object(s, 'sources', 'SourceID', 'Organization')
    
    
def add_qualifiers():
    q1 = {'QualifierCode':'T',
         'QualifierDescription':'Trace of snow'}
    q1_id = db_save.add_odm_object(q1, 'qualifiers', 'QualifierID', 'QualifierCode')
    q2 = {'QualifierCode':'P',
          'QualifierDescription':'Missing presumed zero'}
    q2_id = db_save.add_odm_object(q2, 'qualifiers', 'QualifierID', 'QualifierCode')
    q3 = {'QualifierCode':'A',
          'QualifierDescription':'approved value'}
    q3_id = db_save.add_odm_object(q3, 'qualifiers', 'QualifierID', 'QualifierCode')
    return {'T': q1_id, 'P': q2_id, 'A': q3_id}

def add_ghcn_site_odm(site_obj):
    s = {'SiteCode':site_obj['id'],
         'SiteName':site_obj['name'],
         'Latitude':site_obj['latitude'],
         'Longitude':site_obj['longitude'],
         'LatLongDatumID': 3,
         'SiteType':'Atmosphere',
         'Elevation_m':site_obj['elevation'],
         'VerticalDatum':'MSL',
         'State':site_obj['state'],
         'Comments':site_obj['country']}
    st_id = db_save.add_odm_object(s, 'sites', 'SiteID', 'SiteCode')
    return st_id
    
    
def add_ghcn_snow_odm(site_obj, site_id, variable_id, qualifiers, source_id):
    sitecode = site_obj['id']
    snodat = ulmo.ncdc.ghcn_daily.get_data(sitecode, elements='SNWD', update=False, as_dataframe=True)
    
    #find date range for required inserting
    db_range = db_save.get_odm_value_range(site_id, variable_id)
    db_start = db_range['start']
    db_end = db_range['end']
    
    dv_list = []
    append = dv_list.append
    for date, row in snodat['SNWD'].iterrows():
        
        dtime = date.start_time
        if (dtime < db_start or dtime > db_end):
            #getting the correct qualifier id
            mflag = row['mflag']
            dvalu = row['value']
            
            dtime_iso = dtime.isoformat().split('T')[0]
            qualifier_id = qualifiers['A']
            if mflag == 'T':
                qualifier_id = qualifiers['T']
            if dvalu < 0 or math.isnan(dvalu):
                qualifier_id = qualifiers['P']
                dvalu = -9999
            
            dv = {'DataValue':dvalu,
              'LocalDateTime': dtime_iso,
              'UTCOffset': 0,
              'DateTimeUTC': dtime_iso,
              'SiteID': site_id,
              'VariableID': variable_id,
              'CensorCode':'nc',
              'QualifierID': qualifier_id,
              'MethodID': 1, #no method specified
              'SourceID': 1, #no method specified
              'QualityControlLevelID': 1} #quality controlled data}
            append(dv)
        
    db_save.add_values_odm(dv_list)
    #update series catalog
    return dv_list

def save_snow_all():
    #get all the stations
    all_st = ulmo.ncdc.ghcn_daily.get_stations()

    for st_code in all_st:
        site_from_db = db_save.get_site_id(st_code)
        if site_from_db:
            continue
        st_obj = all_st[st_code]
        sno_data = []
        try:
            sno_data = ulmo.ncdc.ghcn_daily.get_data(st_code, elements='SNWD', update=False, as_dataframe=True)
        except:
            print "unable to retrieve snow_data " + st_code
        if (len(sno_data) > 0):        
            ts_list2 = []
            sno = sno_data['SNWD']
            sno2 = sno['value'].dropna()       
            #now get the site id and save site if required
            site_from_db = db_save.get_site_id(st_code)
            if site_from_db == None:
                site_id = db_save.add_site(st_code, st_obj, 1)
            else:
                site_id = site_from_db[0]
            print site_id
            if site_id > SITE_ID_SKIP and site_id <= SITE_ID_MAX:
                #check for NaN!
                for dat, val in sno2.iteritems():
                    iso = dat.start_time.isoformat()
                    dat_s = iso.strip().split('T')
                    dat2 = dat_s[0]
                    val2 = {'time': dat2, 'site_id': site_id, 'qualifier': 1, 'val': round(val/10)}
                    if val2['val'] > 0:
                        ts_list2.append(val2)

                if len(ts_list2) > 0:
                    try:
                        db_save.add_values(ts_list2)
                        print st_code + ' ' + st_obj['name'] + ' saved: ' + str(len(ts_list2))	
                    except:
                        print "cannot save values to db"				

				
if __name__ == "__main__":
    db_save.DB_CONNECTION = DB_CONNECTION
    save_snow_all()	
