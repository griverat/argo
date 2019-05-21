#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Tue May 21 09:38:40 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

from scipy.interpolate import PchipInterpolator
from dask.diagnostics import ProgressBar
import xarray as xr
import pandas as pd
import numpy as np
import gsw, os


def grid_data(data_file, ix, dfile, grid = np.arange(0,2001,1)):
    depths = gsw.conversions.z_from_p(data_file.PRES[ix].data, data_file.LATITUDE[ix].data)
    temp = data_file.TEMP[ix].data
    salt = data_file.PSAL[ix].data
    mask = ~np.isnan(temp)
    mask[np.where(depths) == 0] = False
    mask[np.isnan(depths)] = False
    if temp[mask].size ==1:
        return np.full_like(grid, np.nan, dtype=np.double), np.full_like(grid, np.nan, dtype=np.double)
    else:
        try:
            func_t = PchipInterpolator(-depths[mask],temp[mask])#, kind='linear',fill_value=np.nan,bounds_error=False)
            func_s = PchipInterpolator(-depths[mask],salt[mask])#, kind='linear',fill_value=np.nan,bounds_error=False)
        except:
            print('Error on file {}'.format(dfile))
            return np.full_like(grid, np.nan, dtype=np.double), np.full_like(grid, np.nan, dtype=np.double)
    new_grid = np.where(grid>-depths[mask][-1],np.nan,grid)
    new_grid[np.where(grid<-depths[mask][0])] = np.nan
    new_temp = func_t(new_grid)
    new_salt = func_s(new_grid)
    return new_temp, new_salt

def nc_save(prof_number, lat, lon, date, temp, tanom, salt, outdir, grid=np.arange(0,2001,1)):
    temp = np.array([[[temp]]])
    tanom = np.array([[[tanom]]])
    salt = np.array([[[salt]]])
    to_write = xr.Dataset({'temperature': (['date','lat','lon','depth'],temp),
                           'temp_anom': (['date','lat','lon','depth'],tanom),
                           'psal':(['date','lat','lon','depth'],salt),
                           'lat_p':(['date'],np.array([lat])),
                           'lon_p':(['date'],np.array([lon]))},
                         coords={'date':np.array([date]),
                                 'lat':np.array([0]),
                                 'lon':np.array([0]),
                                 'depth':grid})
    to_write.lat.attrs['units'] = 'degrees_north'
    to_write.lon.attrs['units'] = 'degrees_east'
    to_write.depth.attrs['units'] = 'm'
    return to_write

def get_first_date(argo_number, template):
    argo_traj = xr.open_dataset(template.format(argo_number))
    first_day = pd.to_datetime(argo_traj.JULD[0].data).date()
    return first_day

def crop_list(argo_number, traj_dir, argo_dir):
    fday_ = get_first_date(argo_number, os.path.join(traj_dir,'{}_Rtraj.nc'))
    fday = '{:%Y%m%d}_prof.nc'.format(fday_)
    argo_files = [x for x in os.listdir(argo_dir) if x.endswith('_prof.nc')]
    ix = argo_files.index(fday)
    return argo_files[ix:], fday_

def build_profile(argo_number, traj_dir, argo_dir, outdir, clim):
    grid=np.arange(0,2001,1)
    files,fday = crop_list(argo_number,traj_dir, argo_dir)
    with ProgressBar():
        print('Loading daily climatology')
        clim = clim.sel(time=slice(fday,'2019-12-31')).load()
    files = [os.path.join(argo_dir,x) for x in files]
    container = []
    for dfile in files:
        data = xr.open_dataset(dfile)
        if argo_number in data.PLATFORM_NUMBER.data.astype(np.int):
            ix = np.where(data.PLATFORM_NUMBER.data.astype(np.int) == argo_number)[0]
            if ix.size > 1:
                for idx in ix:
                    temp, salt = grid_data(data, idx, dfile)
                    lat, lon = data.LATITUDE[idx].data, data.LONGITUDE[idx].data
                    date = data.JULD[idx].data
                    day = clim.sel(time=pd.to_datetime(date).date(),lat=lat,lon=lon+360, method='nearest')#.mean(dim=['lat','lon'])
                    day = day.interp(level=grid).data
                    container.append(nc_save(argo_number, lat, lon, date, temp, temp-day, salt, outdir, grid))
            else:
                ix = ix[0]
                temp, salt = grid_data(data, ix, dfile)
                lat, lon = data.LATITUDE[ix].data, data.LONGITUDE[ix].data
                date = data.JULD[ix].data
                day = clim.sel(time=pd.to_datetime(date).date(),lat=lat,lon=lon+360, method='nearest')#.mean(dim=['lat','lon'])
                day = day.interp(level=grid).bfill(dim='level').data
                container.append(nc_save(argo_number, lat, lon, date, temp, temp-day,salt, outdir, grid))
        else:
            continue
    return xr.merge(container)

def wrap_profile(profiler,clims,*args):
    print(f'## STARING COMPUTATION OF ARGO PROFILER N°{profiler}\n')
    for source, clim_data in clims.items():
        print(f'\nBuilding profile with {source} climatology')
        out_profile = build_profile(profiler,TRAJ_DIR, ARGO_DIR, OUTPUT_DIR, clim_data)
        out_profile.resample({'date':'1D'}).mean(dim='date').to_netcdf(os.path.join(OUTPUT_DIR,f'{profiler}_{source}.nc'))

def main(prof_file, TRAJ_DIR, ARGO_DIR, OUTPUT_DIR, clims):
    prof_list = np.loadtxt(prof_file, dtype=int)
    if prof_list.size == 1:
        prof_list = [prof_list]
    for profiler in prof_list:
        wrap_profile(profiler,clims,TRAJ_DIR, ARGO_DIR, OUTPUT_DIR)

if __name__ == '__main__':
    ARGO_DIR = '/data/datos/ARGO/data/'
    TRAJ_DIR = '/data/users/grivera/ARGO-traj/'
    OUTPUT_DIR = '/data/users/grivera/ARGO-prof'
    PROF_FILE = '/home/grivera/GitLab/argo/Output/paita.txt'

    print('Opening GODAS clim')
    godas_clim = xr.open_mfdataset('/data/users/grivera/GODAS/clim/daily/*.godas_dayclim.nc').pottmp -273
    print('Opening IMARPE clim')
    imarpe_clim = xr.open_mfdataset('/data/users/grivera/IMARPE/clim/daily/*.imarpe_dayclim.nc').temp
    print('Opening SODA clim')
    soda_clim = xr.open_mfdataset('/data/users/grivera/SODA/clim/daily/*.soda_dayclim.nc').temp
    clims = dict(godas=godas_clim, imarpe=imarpe_clim,soda=soda_clim)
    print('Climatologies loaded')
    
    print('\n\n### Starting computation ###\n')
    main(PROF_FILE, TRAJ_DIR, ARGO_DIR, OUTPUT_DIR, clims)
