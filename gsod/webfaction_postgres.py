import psycopg2
import gsod_save_snow
import db_save

db_save.DB_CONNECTION = 'postgresql+psycopg2://snow:snow@127.0.0.1/snow'
gsod_save_snow.NCDC_GSOD_DIR = '/home/keskari/gsod_data'
stations = gsod_save_snow.get_stations()
for year in range(2013,1929,-1):
    gsod_save_snow.save_gsod_snow_year(stations, year, db_save.DB_CONNECTION)
    print(year)
