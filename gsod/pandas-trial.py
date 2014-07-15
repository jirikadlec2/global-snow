# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 15:35:53 2014

@author: Jiri
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

s = pd.Series([1,3,5,np.nan,6,8])

dates = pd.date_range('20130101',periods=6)
df = pd.DataFrame(np.random.randn(6,4), index=dates, columns=list('ABCD'))
df2 = pd.DataFrame({ 'A' : 1.,
                     'B' : pd.Timestamp('20130102'),
                     'C' : pd.Series(1, index=list(range(4)),dtype='float32'),
                     'D' : np.array([3] * 4, dtype='int32'),
                     'E' : 'foo' })
                     
df.head()
df.tail(2)
df.index
df.columns
df.values
df.sort_index(axis=1, ascending=False)
df['20130102':'20130104']
df.loc[dates[0]]
df.loc[:,['A','D']]

df.loc['20130102':'20130104',['A','B']]
df.loc['20130102',['A','B']]

df.loc[dates[0],'A']
df.iloc[3:5,0:2]
df.iloc[[1,2,4],[0,2]]

df[df.A > 0]

df2 = df.copy()
df2['E']=['one', 'one','two','three','four','three']
df2[df2['E'].isin(['two','four'])]

s1 = pd.Series([1,2,3,4,5,6],index=pd.date_range('20130102',periods=6))

df.at[dates[0],'A'] = 0