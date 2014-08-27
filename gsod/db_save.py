# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 09:39:06 2014

@author: Jiri
"""
#import pymysql
#import psycopg2
import datetime
from sqlalchemy import *
import db_config


def db_connection():
    return db_config.DB_CONNECTION
    

def test_sql_alchemy():
    db = create_engine(db_connection())
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
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    t = Table(table_name, metadata, autoload=True)
    s = t.select(t.c[unique_column] == obj[unique_column])    
    rs = s.execute()
    r = rs.fetchone()
    if not r:
        i = t.insert()
        i_res = i.execute(obj)
        v_id = i_res.inserted_primary_key[0]
    else:
        v_id = r[primary_key] 
        
    conn.close()
    return v_id

def get_odm_object(table_name, primary_key, object_id):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    t = Table(table_name, metadata, autoload=True)
    s = t.select(t.c[primary_key] == object_id)    
    rs = s.execute()
    r = rs.fetchone()
    conn.close()
    return r


def add_site(st_code, st, ghcn=0):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
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
    else:
        st_id = r['site_id']
        
    conn.close()
    return st_id


def add_sites(stations):
    fields = ['name', 'latitude', 'longitude', 'elevation']
    for key, val in stations.iteritems():
        valid = check_site(val, fields)
        if valid:
            db_id = add_site(key, val)
            val['id'] = db_id


def get_sites():
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    sites_t = Table('sites', metadata, autoload=True)
    s = sites_t.select()
    rs = s.execute()
    r = list(rs.fetchall())
    conn.close()
    return r


def add_values_odm(values_list):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    values_t = Table('datavalues', metadata, autoload=True)
    i = values_t.insert()
    i.execute(values_list)
    conn.close()
    
def update_series_catalog(st_id, var_id, meth_id, src_id, qc_id, values_list):
    start_date = values_list[0]['LocalDateTime']
    end_date = values_list[-1]['LocalDateTime']
    
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    #get site information
    site = get_odm_object('sites', 'SiteID', st_id)
    #get variable info
    vari = get_odm_object('variables', 'VariableID', var_id)
    #get time unit, variable unit
    vari_unit = get_odm_object('units', 'unitsID', vari['VariableunitsID'])
    time_unit = get_odm_object('units', 'unitsID', vari['TimeunitsID'])
    #get source info
    src = get_odm_object('sources', 'SourceID', src_id)
    #get method info
    meth = get_odm_object('methods', 'MethodID', meth_id)
    #get qualityControlLevel
    qc = get_odm_object('qualitycontrollevels', 'QualityControlLevelID', qc_id)
    
    t = Table('seriescatalog', metadata, autoload=True)
    s = t.select(t.c.SiteID == st_id and t.c.VariableID == variable_id)
    rs = s.execute()
    r = rs.fetchone()
    if not r: #insert
        obj = {'SiteID':st_id,
               'SiteCode':site['SiteCode'],
               'SiteName':site['SiteName'],
               'SiteType':site['SiteType'],
               'VariableID':var_id,
               'VariableCode':vari['VariableCode'],
               'VariableName':vari['VariableName'],
               'Speciation':vari['Speciation'],
               'VariableunitsID':vari['VariableunitsID'],
               'VariableunitsName':vari_unit['unitsName'],
               'SampleMedium':vari['SampleMedium'],
               'ValueType':vari['ValueType'],
               'TimeSupport':vari['TimeSupport'],
               'TimeunitsID':vari['TimeunitsID'],
               'TimeunitsName':time_unit['unitsName'],
               'DataType':vari['DataType'],
               'GeneralCategory':vari['GeneralCategory'],
               'MethodID':meth_id,
               'MethodDescription':meth['MethodDescription'],
               'SourceID':src_id,
               'Organization':src['Organization'],
               'SourceDescription':src['SourceDescription'],
               'Citation':src['Citation'],
               'QualityControlLevelID':qc_id,
               'QualityControlLevelCode':qc['QualityControlLevelCode'],
               'BeginDateTime':start_date,
               'EndDateTime':end_date,
               'BeginDateTimeUTC':start_date,
               'EndDateTimeUTC':end_date,
               'ValueCount':len(values_list)}
        i = t.insert()
        i.execute(obj)
    else:
        start_end = get_odm_value_range(st_id, var_id)
        db_start = start_end['start']
        db_end = start_end['end']
        if start_date < db_start:
            db_start = start_date
        if end_date > db_end:
            db_end = end_date
            
        obj = {'BeginDateTime':db_start,
               'EndDateTime':db_end,
               'BeginDateTimeUTC':db_start,
               'EndDateTimeUTC':db_end,
               'ValueCount':len(values_list)}
        i = t.update().where(t.c.SiteID==st_id and t.c.VariableID==var_id)
        i.execute(obj)
    conn.close()
    
    
def get_odm_value_range(st_id, variable_id):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    t = Table('seriescatalog', metadata, autoload=True)
    s = t.select(t.c.SiteID == st_id and t.c.VariableID == variable_id)
    rs = s.execute()
    r = rs.fetchone()
    if r:
        ret = {'start': r.BeginDateTime, 'end': r.EndDateTime}
    else:
        ret ={'start': datetime.datetime(1900,1,1, 0, 0, 0), 
                'end': datetime.datetime(1900, 1, 1, 0, 0, 0)}
    conn.close()
    return ret
        

def add_values(ts):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    values_t = Table('snow', metadata, autoload=True)
    i = values_t.insert()
    i.execute(ts)
    conn.close()

def get_values(st_id):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    v_t = Table('snow', metadata, autoload=True)
    s = v_t.select(v_t.c.site_id == st_id)
    rs = s.execute()
    r = list(rs.fetchall())
    conn.close()
    return r
    

def get_site_id(st_code):
    db = create_engine(db_connection())
    conn = db.connect()
    metadata = MetaData(conn)
    sites_t = Table('sites', metadata, autoload=True)
    s = sites_t.select(sites_t.c.site_code == st_code)
    rs = s.execute()
    r = rs.fetchone()
    conn.close()
    return r

