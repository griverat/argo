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
from distributed.diagnostics.progressbar import progress
from scipy.interpolate import PchipInterpolator
from dask import delayed
import xarray as xr
import numpy as np
import pandas as pd
import dask.array as da
import os
import json
import sys
import gsw

with open("./../paths.json") as f:
    paths = json.load(f)


def filter_data(data, lat, lon, time):
    filt = data.query("(date>=@time[0])&(date<=@time[1])")
    filt = filt.query("(lat>={})&(lat<={})".format(*lat))
    filt = filt.query("(lon>={})&(lon<={})".format(*lon))
    return filt


@delayed
def get_temp_anom(fname, prof, clim, grid=np.arange(0, 2001, 2.0)):
    with xr.open_dataset(fname) as data:
        data = data.load()
    temp = data.TEMP[prof].data
    depth = gsw.conversions.z_from_p(data.PRES[prof], data.LATITUDE[prof])
    mask = ~np.isnan(temp)
    mask[np.where(depth == 0)] = False
    if temp[mask].size <= 30:
        return np.full_like(np.array([grid, grid]), np.nan, dtype=np.double)
    try:
        func = PchipInterpolator(-depth[mask], temp[mask])
    except Exception:
        return np.full_like(np.array([grid, grid]), np.nan, dtype=np.double)
    new_grid = np.where(grid > -depth[mask][-1], np.nan, grid)
    new_grid[np.where(grid < -depth[mask][0])] = np.nan
    new_data = func(new_grid)

    day = clim.interp(level=grid)
    data = np.array([new_data - day.data, new_data])
    return data


@delayed
def dastack(data):
    return np.stack(data, axis=0)


def update_nc():
    pass


def save_nc(argodb, argo_data, filename, vname, lon, lat, grid, outdir):
    # argo_data = argo_data.compute()
    argo_count = argodb.groupby("date").size().resample("1D").asfreq().values
    print("Resampling to daily data")
    argo_data = (
        xr.DataArray(
            argo_data,
            coords=[argodb.date.values, grid.astype(np.int64)],
            dims=["time", "level"],
        )
        .resample(time="1D")
        .mean(dim="time")
    )
    mlon = np.mean(lon)
    mlat = np.mean(lat)
    print("Creating dataset")
    argo_time = argo_data.time.values
    argo_data = np.array([[argo_data.data]])
    argo_data = xr.Dataset(
        {
            vname: (["lat", "lon", "time", "level"], argo_data),
            "prof_count": (["lat", "lon", "time"], np.array([[argo_count]])),
        },
        coords={
            "lon": [mlon],
            "lat": [mlat],
            "time": argo_time,
            "level": grid.astype(np.int64),
        },
    )
    argo_data.lon.attrs["units"] = "degrees_north"
    argo_data.lat.attrs["units"] = "degrees_east"
    argo_data.level.attrs["units"] = "m"
    argo_data.attrs["author"] = "SCAH - IGP"
    print("Saving dataset")
    argo_data.to_netcdf(
        os.path.join(
            outdir,
            "{}_{:.1f},{:.1f}_{:.1f},{:.1f}.nc".format(
                filename, lon[0], lon[1], lat[0], lat[1]
            ),
        )
    )
    print("saving done\n")


def get_fn(date, ARGO_DIR, temp):
    return os.path.join(ARGO_DIR, temp.format(date))


def setup_cluster():
    cluster = LocalCluster(n_workers=6, threads_per_worker=1)
    client = Client(cluster)
    return client


def main(lat, lon, time):
    client = setup_cluster()
    print(client)
    GODAS_GLOB = "/data/users/grivera/GODAS/clim/daily/*.godas_dayclim.nc"

    argodb = pd.read_csv(paths["ARGO_DB"], parse_dates=[0])
    grid = np.arange(0, 2001, 2.0)
    newdf = filter_data(argodb, lat, lon, time)
    newdf.loc[:, "fname"] = newdf["date"].apply(
        get_fn, args=(paths["ARGO_DATA"], "{:%Y%m%d}_prof.nc")
    )
    newdf = newdf.sort_values("date")
    print(
        "\nLoading GODAS climatology from {:%Y-%m-%d} to {:%Y-%m-%d}".format(
            newdf.date.iloc[0], newdf.date.iloc[-1]
        )
    )
    godas_clim = xr.open_mfdataset(GODAS_GLOB, parallel=True).pottmp - 273
    godas_clim = (
        godas_clim.sel(
            time=slice(newdf.date.iloc[0], newdf.date.iloc[-1]),
            lat=slice(lat[0], lat[1]),
            lon=slice(lon[0], lon[1]),
        )
        .mean(dim=["lat", "lon"])
        .persist()
    )
    progress(godas_clim)
    godas_clim = godas_clim.compute()
    print("\nDone \n")
    print("Computing region average")
    new_data = dastack(
        [
            get_temp_anom(r.fname, r.nprof, godas_clim.sel(time=r.date))
            for r in newdf.itertuples()
        ]
    )
    new_data = new_data.persist()
    progress(new_data)
    new_data = new_data.compute()
    print("\nDone\n")
    save_nc(
        newdf,
        new_data[:, 0, :],
        "argo_tanom",
        "tanom",
        lon,
        lat,
        grid,
        paths["ARGO_PATCH_OUT"],
    )
    save_nc(
        newdf,
        new_data[:, 1, :],
        "argo_temp",
        "temp",
        lon,
        lat,
        grid,
        paths["ARGO_PATCH_OUT"],
    )


if __name__ == "__main__":
    lats = [float(sys.argv[1]), float(sys.argv[2])]
    lons = [float(sys.argv[3]), float(sys.argv[4])]
    tran = [str(sys.argv[5]), str(sys.argv[6])]
    main(lats, lons, tran)
    print("\nbeep boop it's all done\n\n")
    # main([-2.5,2.5],[253,260],['1999-01-01', '2019-03-14'])
