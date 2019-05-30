#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Mon Apr 22 08:57:36 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

from datetime import datetime
import pandas as pd
import numpy as np


def filter_date(prof,argo_db,days):
    delta = pd.Timedelta(days,'D')
    argo_db = argo_db.query('(platfn==@prof)')
    today = argo_db.date.iloc[-1]
    st_date = today-delta
    filtered = argo_db.query('(date>@st_date)&(lat>-10)&(lat<0)&(lon>270)&(lon<290)').reset_index(drop=True)[['date','lat','lon']]
    return filtered


def build_ts(end_date,tbefore,days):
    delta = pd.Timedelta(days,'D')
    tbefore = pd.Timedelta(tbefore,'D')
    lim_date = end_date - tbefore
    new_time = end_date
    date_lims = []
    date_lims.append(new_time)
    while new_time > lim_date:
        new_time -= delta
        date_lims.append(new_time)
    date_lims.append(lim_date)
    return date_lims


def group_dates(filter_db,day_thres):
    today = pd.to_datetime(datetime.today().replace(hour=0,minute=0,second=0,microsecond=0))
    date_ranges = build_ts(today, 365, 30)
    for i in range(len(date_ranges)):
        dbefore = date_ranges[i]
        try:
            dafter = date_ranges[i+1]
            ix_ = filter_db.query('(date<=@dbefore)&(date>@dafter)').index
        except:
            print("Reached final date")
            ix_ = filter_db.query('date<@dbefore').index

        for ix in ix_:
            filter_db.loc[ix,'class'] = i
    return filter_db


def check_update(old_file,new_date):
    try:
        old_data = pd.read_csv(old_file, sep=' ', parse_dates=[0])
    except:
        print("Old file not found.\nCreating file")
        return True
    old_date = old_data.iloc[-1,0]
    if old_date == new_date:
        print("No new data found")
        return False
    else:
        print("New data found")
        return True


if __name__ == "__main__":
    prof_list = np.loadtxt('/home/grivera/GitLab/argo/Output/paita.txt', dtype=int)
    argo_db = pd.read_csv('/data/users/grivera/ARGO-latlon/latlontemp.txt',
                            parse_dates=[0]).sort_values('date').reset_index(drop=True)
    argo_filter = filter_date(prof_list,argo_db,365)
    argo_filter = group_dates(argo_filter,30)
    filename = '/data/users/grivera/ARGO-prof/{}-traj{}.txt'
    if check_update(filename.format(prof_list,1),argo_filter.date.iloc[-1]):
        for i in range(1,3):
            argo_filter.to_csv(filename.format(prof_list,i), header=None, index=None, sep=' ',
                            float_format='%.5f')
