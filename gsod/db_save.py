# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 09:39:06 2014

@author: Jiri
"""
#import pymysql
import psycopg2
from sqlalchemy import *

#DB_CONNECTION = 'mysql+pymysql://root:@127.0.0.1/snow'
DB_CONNECTION = 'postgresql+psycopg2://snow:snow@127.0.0.1/snow'

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
    n_saved = 0
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

