# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 09:39:06 2014

@author: Jiri
"""
#import pymysql
#import psycopg2
import datetime
from sqlalchemy import *

DB_CONNECTION = 'mysql+pymysql://root:@127.0.0.1/ogimet-snow'
#DB_CONNECTION = 'postgresql+psycopg2://snow:snow@127.0.0.1/snow'

def test_sql_alchemy():
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    db.echo = True
    myT = Table('test', metadata,
                Column('user_id', Integer, primary_key=True),
                Column('name', String(40)))
    myT.create()
    i = myT.insert()
    i.execute({'name': 'George'})


def check_site(st, fields):
    valid = True
    for key, val in st.iteritems():
        if key in fields and not val:
            valid = False
    return valid
    

def add_odm_object(obj, table_name, primary_key, unique_column):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    t = Table(table_name, metadata, autoload=True)
    s = t.select(t.c[unique_column] == obj[unique_column])    
    rs = s.execute()
    r = rs.fetchone()
    if not r:
        i = t.insert()
        i_res = i.execute(obj)
        v_id = i_res.inserted_primary_key[0]
        return v_id
    else:
        return r[primary_key]   
    

def get_odm_object(table_name, primary_key, object_id):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    t = Table(table_name, metadata, autoload=True)
    s = t.select(t.c[primary_key] == object_id)    
    rs = s.execute()
    r = rs.fetchone()
    return r


def add_site(st_code, st, ghcn=0):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    sites_t = Table('sites', metadata, autoload=True)
    s = sites_t.select(sites_t.c.site_code == st_code)
    rs = s.execute()
    r = rs.fetchone()
    if not r:
        i = sites_t.insert()
        insert_res = i.execute({'site_name': st['name'],
                                'site_code': st_code,
                                'lat': st['latitude'],
                                'lon': st['longitude'],
                                'elev': st['elevation'],
								'ghcn': ghcn})
        st_id = insert_res.inserted_primary_key[0]
        return st_id
    else:
        return r['site_id']


def add_sites(stations):
    fields = ['name', 'latitude', 'longitude', 'elevation']
    for key, val in stations.iteritems():
        valid = check_site(val, fields)
        if valid:
            db_id = add_site(key, val)
            val['id'] = db_id


def get_sites():
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    sites_t = Table('sites', metadata, autoload=True)
    s = sites_t.select()
    rs = s.execute()
    r = list(rs.fetchall())
    return r


def add_values_odm(values_list):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    values_t = Table('datavalues', metadata, autoload=True)
    i = values_t.insert()
    i.execute(values_list)
    
def update_series_catalog(site, variable, method, source, qc, values_list):
    start_date = values_list[0]['LocalDateTime']
    end_date = values_list[-1]['LocalDateTime']
    
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    t = Table('seriescatalog', metadata, autoload=True)
    s = t.select(t.c.SiteID == st_id and t.c.VariableID == variable_id)
    rs = s.execute()
    r = rs.fetchone()
    if not r: #insert
        obj = {'SiteID':site['SiteID'],
               'SiteCode':site['SiteCode'],
               'SiteName':site['SiteName'],
               'SiteType':site['SiteType'],
               'VariableID':variable['VariableID'],
               'VariableCode':variable['VariableCode'],
               'VariableName':variable['VariableName'],
               'Speciation':variable['Speciation'],
               'VariableunitsID':variable['VariableunitsID'],
               'VariableunitsName':variable['VariableunitsName'],
               'SampleMedium':variable['SampleMedium'],
               'ValueType':variable['ValueType'],
               'TimeSupport':variable['TimeSupport'],
               'TimeunitsID':variable['TimeUnitsID'],
               'TimeunitsName':variable['TimeunitsName'],
               'DataType':variable['DataType'],
               'GeneralCategory':variable['GeneralCategory'],
               'MethodID':method['MethodID'],
               'MethodDescription':method['MethodDescription']}
    
    
def get_odm_value_range(st_id, variable_id):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    t = Table('seriescatalog', metadata, autoload=True)
    s = t.select(t.c.SiteID == st_id and t.c.VariableID == variable_id)
    rs = s.execute()
    r = rs.fetchone()
    if r:
        return {'start': r.BeginDateTime, 'end': r.EndDateTime}
    else:
        return {'start': datetime.datetime(1900,1,1, 0, 0, 0), 
                'end': datetime.datetime(1900, 1, 1, 0, 0, 0)}
        

def add_values(ts):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    values_t = Table('snow', metadata, autoload=True)
    i = values_t.insert()
    i.execute(ts)
    

def get_values(st_id):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    v_t = Table('snow', metadata, autoload=True)
    s = v_t.select(v_t.c.site_id == st_id)
    rs = s.execute()
    r = list(rs.fetchall())
    return r
    

def get_site_id(st_code):
    db = create_engine(DB_CONNECTION)
    metadata = MetaData(db)
    sites_t = Table('sites', metadata, autoload=True)
    s = sites_t.select(sites_t.c.site_code == st_code)
    rs = s.execute()
    r = rs.fetchone()
    return r

