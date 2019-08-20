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
import argparse
import gsw
import json
import os

with open("./../paths.json") as f:
    paths = json.load(f)


def check_folder(base_path, name=None):
    if name is not None:
        out_path = os.path.join(base_path, str(name))
    else:
        out_path = base_path
    if not os.path.exists(out_path):
        os.mkdirs(name)


def test_qc(qc):
    siz = qc.size
    mask = qc == 4
    if mask.sum() > siz / 2:
        return np.full_like(qc, True, dtype=np.bool)
    else:
        return qc


def grid_data(data_file, ix, dfile, grid=np.arange(0, 2001, 1)):
    temp_qc = test_qc(data_file.TEMP_QC[ix].astype(np.float))
    psal_qc = test_qc(data_file.PSAL_QC[ix].astype(np.float))
    pres_qc = test_qc(data_file.PRES_QC[ix].astype(np.float))
    depths = gsw.conversions.z_from_p(
        data_file.PRES[ix].where(pres_qc != 4).data, data_file.LATITUDE[ix].data
    )
    temp = data_file.TEMP[ix].where(temp_qc != 4).interpolate_na(dim="N_LEVELS").data
    salt = data_file.PSAL[ix].where(psal_qc != 4).interpolate_na(dim="N_LEVELS").data
    mask = ~np.isnan(temp)
    mask[np.where(depths) == 0] = False
    mask[np.isnan(depths)] = False
    new_grid = np.where(grid > -depths[mask][-1], np.nan, grid)
    new_grid[np.where(grid < -depths[mask][0])] = np.nan
    if temp[mask].size == 1:
        return (
            np.full_like(grid, np.nan, dtype=np.double),
            np.full_like(grid, np.nan, dtype=np.double),
        )
    else:
        try:
            func_t = PchipInterpolator(-depths[mask], temp[mask])
            new_temp = func_t(new_grid)
        except:
            print("TEMP: Error on file {}".format(dfile))
            new_temp = np.full_like(grid, np.nan, dtype=np.double)
        try:
            func_s = PchipInterpolator(-depths[mask], salt[mask])
            new_salt = func_s(new_grid)
        except:
            print("PSAL: Error on file {}".format(dfile))
            new_salt = np.full_like(grid, np.nan, dtype=np.double)

    return new_temp, new_salt


def nc_save(
    prof_number, lat, lon, date, temp, tanom, salt, outdir, grid=np.arange(0, 2001, 1)
):
    temp = np.array([[[temp]]])
    tanom = np.array([[[tanom]]])
    salt = np.array([[[salt]]])
    to_write = xr.Dataset(
        {
            "temperature": (["time", "lat", "lon", "level"], temp),
            "temp_anom": (["time", "lat", "lon", "level"], tanom),
            "psal": (["time", "lat", "lon", "level"], salt),
            "lat_p": (["time"], np.array([lat])),
            "lon_p": (["time"], np.array([lon])),
        },
        coords={
            "time": np.array([date]),
            "lat": np.array([0]),
            "lon": np.array([0]),
            "level": grid,
        },
    )
    to_write.lat.attrs["units"] = "degrees_north"
    to_write.lon.attrs["units"] = "degrees_east"
    to_write.level.attrs["units"] = "m"
    return to_write


def crop_list(argo_number, argo_db, argo_dir):
    sbt_db = (
        argo_db.query("platfn==@argo_number")
        .sort_values(by="date")
        .reset_index(drop=True)
    )
    fday = "{:%Y%m%d}".format(sbt_db.iloc[0].date)
    argo_files = sbt_db["date"].apply(lambda x: "{:%Y%m%d}_prof.nc".format(x))
    return argo_files, fday


def build_profile(argo_number, argo_db, argo_dir, outdir, clim):
    grid = np.arange(0, 2501, 1)
    files, fday = crop_list(argo_number, argo_db, argo_dir)
    with ProgressBar():
        print("Loading daily climatology")
        clim = clim.sel(time=slice(fday, "2019-12-31")).load()
    files = [os.path.join(argo_dir, x) for x in files]
    container = []
    for dfile in files:
        data = xr.open_dataset(dfile)
        if argo_number in data.PLATFORM_NUMBER.data.astype(np.int):
            ix = np.where(data.PLATFORM_NUMBER.data.astype(np.int) == argo_number)[0]
            if ix.size > 1:
                for idx in ix:
                    temp, salt = grid_data(data, idx, dfile, grid)
                    lat, lon = data.LATITUDE[idx].data, data.LONGITUDE[idx].data
                    date = data.JULD[idx].data
                    day = clim.sel(
                        time=pd.to_datetime(date).date(),
                        lat=lat,
                        lon=lon + 360,
                        method="nearest",
                    )
                    day = day.interp(level=grid).data
                    container.append(
                        nc_save(
                            argo_number,
                            lat,
                            lon,
                            date,
                            temp,
                            temp - day,
                            salt,
                            outdir,
                            grid,
                        )
                    )
            else:
                ix = ix[0]
                temp, salt = grid_data(data, ix, dfile, grid)
                lat, lon = data.LATITUDE[ix].data, data.LONGITUDE[ix].data
                if lon < 0:
                    lon += 360
                date = data.JULD[ix].data
                day = (
                    clim.sel(time=pd.to_datetime(date).date())
                    .ffill(dim="lat")
                    .sel(lat=lat, lon=lon, method="nearest")
                )
                day = day.interp(level=grid).bfill(dim="level").data
                if (lat < clim.lat.data.min()) or (lon < clim.lon.data.min()):
                    day[:] = np.nan
                container.append(
                    nc_save(
                        argo_number,
                        lat,
                        lon,
                        date,
                        temp,
                        temp - day,
                        salt,
                        outdir,
                        grid,
                    )
                )
        else:
            continue
    return xr.merge(container)


def wrap_profile(profiler, clims, argo_db, ARGO_DIR, OUTPUT_DIR):
    print(f"\n\n## STARING COMPUTATION OF ARGO PROFILER N°{profiler}\n")
    for source, clim_data in clims.items():
        print(f"\nBuilding profile with {source} climatology")
        out_profile = build_profile(profiler, argo_db, ARGO_DIR, OUTPUT_DIR, clim_data)
        out_profile = out_profile.resample({"time": "1D"}).mean(dim="time")
        out_profile.attrs["platfn"] = profiler
        out_profile.to_netcdf(os.path.join(OUTPUT_DIR, f"{profiler}_{source}.nc"))


def main(prof_file, DB_DIR, ARGO_DIR, OUTPUT_DIR, clims):
    prof_list = np.loadtxt(prof_file, dtype=int)
    argo_db = (
        pd.read_csv(os.path.join(DB_DIR, "argo_latlon.txt"), parse_dates=[0])
        .sort_values("date")
        .reset_index(drop=True)
    )
    if prof_list.size == 1:
        prof_list = [prof_list]
    for profiler in prof_list:
        wrap_profile(profiler, clims, argo_db, ARGO_DIR, OUTPUT_DIR)


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description="Get the vertical temperature and salinity profiles of an ARGO float"
    )
    parser.add_argument(
        "proflist", type=str, help="File containing ARGO floats id. One per row"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":

    args = getArgs()
    PROF_FILE = args.proflist

    print("Opening GODAS clim")
    godas_clim = (
        xr.open_mfdataset(
            "/data/users/grivera/GODAS/clim/daily/*.godas_dayclim.nc"
        ).pottmp
        - 273
    )
    print("Opening IMARPE clim")
    imarpe_clim = xr.open_mfdataset(
        "/data/users/grivera/IMARPE/clim/daily/*.imarpe_dayclim.nc"
    ).temp
    print("Opening SODA clim")
    soda_clim = xr.open_mfdataset(
        "/data/users/grivera/SODA/clim/daily/*.soda_dayclim.nc"
    ).temp
    clims = dict(godas=godas_clim, imarpe=imarpe_clim, soda=soda_clim)
    print("Climatologies loaded")

    print("\n\n### Starting computation ###\n")
    check_folder(paths["ARGO_PROF_OUT"])
    main(
        PROF_FILE,
        paths["ARGO_DB_OUT"],
        paths["ARGO_DATA"],
        paths["ARGO_PROF_OUT"],
        clims,
    )
