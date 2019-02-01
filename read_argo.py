#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Fri Jan 11 10:14:43 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2018 Instituto Geofisico del Peru
-----
"""

import os
import sys
import xarray as xr
import pandas as pd
from datetime import datetime

def list_files(ddir, ext):
    return [os.path.join(ddir,x) for x in os.listdir(ddir) if x.endswith(ext)]


def get_prof(data_file,lat_range,lon_range):
    data_file = xr.open_dataset(data_file)
    mask = (data_file.LATITUDE>lat_range[0]) & (data_file.LATITUDE<lat_range[1]) & (data_file.LONGITUDE > lons[0]) & (data_file.LONGITUDE < lons[1])
    platf = data_file.PLATFORM_NUMBER.load()
    plat_num = platf[mask].astype(str)
    data_file.close()
    return plat_num.to_dataframe()

def main(ndates, name, lat_range, lon_range=[-180,180]):
    DIR = '/data/datos/ARGO/data'
    fil = list_files(DIR,'_prof.nc')
    last = fil[-ndates:]
    print('Getting the last {} files'.format(ndates))
    print('First file: {}\n\n'.format(last[0]))
    platf = [get_prof(argo_file, lat_range, lon_range) for argo_file in last]
    platf = pd.concat(platf).reset_index(drop=True).drop_duplicates(subset=['PLATFORM_NUMBER'])
    platf.to_csv(name,sep='\t',header=False, index=None)
    print('Profile list updated.')

if __name__=='__main__':
    ndates = int(sys.argv[1])
    name = str(sys.argv[2])
    lats = [float(sys.argv[3]), float(sys.argv[4])]
    if len(sys.argv) == 7:
        lons = [float(sys.argv[5]), float(sys.argv[6])]
        main(ndates, name, lats, lons)
    else:
        main(ndates, name, lats)
