# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 09:28:37 2014

@author: Jiri
"""

import pymysql
conn = pymysql.connect(host='127.0.0.1', 
                       port=3306,user='root', 
                       passwd='',
                       db='snow')
                       
cur = conn.cursor()
cur.execute("INSERT INTO sites (site_id, site_name, site_code, lat, lon, elev) VALUES(1, 'test', '111-111',50,15,234)")
                      