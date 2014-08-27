# -*- coding: utf-8 -*-
"""
Created on Tue Aug 26 17:14:47 2014

@author: Jiri
"""
import ghcn_save_snow as ghcs
import ulmo

myqual = ghcs.add_qualifiers()
varid = ghcs.add_snow_variable()
srcid = ghcs.add_snow_source()

utah_st = ulmo.ncdc.ghcn_daily.get_stations(country='US', state='UT', elements='SNWD', start_year=2014, end_year=2014, as_dataframe=False)

for myst in utah_st.itervalues():
    mystid = ghcs.add_ghcn_site_odm(myst)
    ghcs.add_ghcn_snow_odm(myst, mystid, varid, myqual, srcid)
    print mystid
