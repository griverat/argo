#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Sun Feb 17 02:03:54 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

from dask.distributed import Client, LocalCluster
from dask.diagnostics import progress
from dask import delayed
import xarray as xr
import os
import gsw
import numpy as np
import pandas as pd
import dask.array as da


def filter_data(data, lat, lon, time):
    max_lat = max_lat
    max_lon = max_lon+1
    filt = data[(data['date']>time[0])&(data['date']<time[1])]
    filt = filt[(filt['lat']>lat[0])&(filt['lat']<lat[1])]
    filt = filt[(filt['lon']>lon[0])&(filt['lon']<lon[1])]
    x_grid = np.arange(lon[0],lon[1],0.5)
    y_grid = np.arange(lat[0],lat[1],0.5)
    return filt, x_grid, y_grid


@delayed
def get_temp_anom(fname,prof,clim,grid):
    data = xr.open_dataset(fname)
    temp = data.TEMP[prof].data
    depth = gsw.conversions.z_from_p(data.PRES[prof],data.LATITUDE[prof])
    mask = ~np.isnan(temp)
    mask[np.where(depth == 0)] = False
    if temp[mask].size ==1:
        return np.full_like(np.array([grid,grid]), np.nan, dtype=np.double)
    try:
        func = PchipInterpolator(-depth[mask],temp[mask])
    except:
        print('Error on file {}'.format(fname))
        return np.full_like(np.array([grid,grid]), np.nan, dtype=np.double)
    new_grid = np.where(grid>-depth[mask][-1],np.nan,grid)
    new_grid[np.where(grid<-depth[mask][0])] = np.nan
    new_data = func(new_grid)
    
    date = pd.to_datetime(data.JULD[prof].data).date()
    lat = data.LATITUDE[prof].data
    lon = data.LONGITUDE[prof].data
    day = clim.sel(time=date)
    day = day.interp(depth=grid)
    return np.array([new_data - day.data, new_data])


@delayed
def dastack(data):
    return da.stack(data,axis=0)


def save_nc(argodb, argo_data, filename, varname, lon, lat, grid,
            outdir='/data/users/grivera/ARGO-patch'):
    argo_data = xr.Dataset({varname:(['lat','lon','time','level'],np.array([[argodata.compute().compute()]]))},
                            coords={'lon':[lon],
                                    'lat':[lat],
                                    'time':argodb.date.values,
                                    'level':grid.astype(np.int64)})
    argo_data = argo_data.resample(time='1D').asfreq()
    argo_data.lon.attrs['units']='degrees_east'
    argo_data.lat.attrs['units']='degrees_north'
    argo_data.level.attrs['units']='m'
    argo_data.to_netcdf(os.path.join(outdir,'{}_{:.1f}-{:.1f}.nc'.format(filename, lon, lat)))


def main(lat,lon,time):
    argodb = pd.read_csv('/home/grivera/GitLab/argo/Profiler_list/Output/latlontemp',
                        parse_dates=[0])
    grid = np.arange(0,2001,2.)
    newdf = filter_data(argodb,lat,lon,time)[0]
    godas_clim = xr.open_dataset('/data/users/grivera/GODAS/godas_dayclim.nc')
    new_data = dastack([get_temp_anom(r.fname,r.nprof,region_mean, grid) for r in newdf.itertuples()])
    new_data = new_data.persist()
    progress(new_data)
    mlon = np.mean(lon)
    mlat = np.mean(lat)
    save_nc(newdf, new_data[:,0,:],'argo_tanom','tanom',mlon,mlat, grid)
    save_nc(newdf, new_data[:,0,:],'argo_temp','temp',mlon,mlat, grid)


if __name__ == '__main__':
    main([-2.5,2.5],[253,260],['1999-01-01', '2019-02-13'])