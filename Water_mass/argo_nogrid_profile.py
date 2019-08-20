#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Wed Jul 31 03:35:10 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

import os
import argparse
import numpy as np
import pandas as pd
import xarray as xr


def crop_list(argo_number, argo_db, argo_dir):
    sbt_db = (
        argo_db.query("platfn==@argo_number")
        .sort_values(by="date")
        .reset_index(drop=True)
    )
    argo_files = sbt_db["date"].apply(lambda x: "{:%Y%m%d}_prof.nc".format(x))
    return argo_files


def fix_lon(data):
    lonattrs = data.LONGITUDE.attrs
    data["LONGITUDE"] = (
        data["LONGITUDE"] + 360 if data["LONGITUDE"] < 0 else data["LONGITUDE"]
    )
    data.LONGITUDE.attrs = lonattrs
    return data


def selprof(argo_file, ix):
    data = argo_file.sel(N_PROF=ix)[
        ["TEMP", "PSAL", "PRES", "LATITUDE", "LONGITUDE", "JULD"]
    ]
    data = fix_lon(data)
    data["N_LEVELS"] = range(data.TEMP.size)
    return data


def build_profile(argo_number, argo_db, argo_dir, outdir):
    files = crop_list(argo_number, argo_db, argo_dir)
    files = [os.path.join(argo_dir, x) for x in files]
    container = []
    for dfile in files:
        argo_file = xr.open_dataset(dfile)
        if argo_number in argo_file.PLATFORM_NUMBER.data.astype(np.int):
            ix = np.where(argo_file.PLATFORM_NUMBER.data.astype(np.int) == argo_number)[
                0
            ]
            if ix.size > 1:
                for idx in ix:
                    container.append(selprof(argo_file, idx))
            else:
                ix = ix[0]
                container.append(selprof(argo_file, ix))
        else:
            continue
    return xr.concat(container, dim="N_PROF")


def main(prof_file, DB_DIR, ARGO_DIR, OUTPUT_DIR):
    prof_list = np.loadtxt(prof_file, dtype=int)
    argo_db = (
        pd.read_csv(os.path.join(DB_DIR, "argo_latlon.txt"), parse_dates=[0])
        .sort_values("date")
        .reset_index(drop=True)
    )
    if prof_list.size == 1:
        prof_list = [prof_list]
    for profiler in prof_list:
        print(f"\n\n## STARING COMPUTATION OF ARGO PROFILER N°{profiler}\n")
        out_profile = build_profile(profiler, argo_db, ARGO_DIR, OUTPUT_DIR)
        out_profile.attrs["platfn"] = profiler
        print("Saving NetCDF")
        out_profile.to_netcdf(os.path.join(OUTPUT_DIR, f"{profiler}_nogrid.nc"))
        print("Done")


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description="Get the vertical temperature and \
                    salinity profiles of an ARGO float \
                    on their original pressure levels"
    )
    parser.add_argument(
        "proflist", type=str, help="File containing ARGO floats id. One per row"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = getArgs(["/home/grivera/GitLab/argo/Output/peru.txt"])

    ARGO_DIR = "/data/datos/ARGO/data/"
    DB_DIR = "/data/users/grivera/ARGO-latlon/"
    OUTPUT_DIR = "/data/users/grivera/ARGO-prof"

    main(args.proflist, DB_DIR, ARGO_DIR, OUTPUT_DIR)
