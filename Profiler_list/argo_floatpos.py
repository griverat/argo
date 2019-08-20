#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Wed Feb 13 09:10:31 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2018 Instituto Geofisico del Peru
-----
"""

from dask.distributed import Client, LocalCluster
from distributed.diagnostics.progressbar import progress
from dask import delayed
import dask.dataframe as dd
import xarray as xr
import pandas as pd
import numpy as np
import json
import os


def check_folder(base_path, name=None):
    if name is not None:
        out_path = os.path.join(base_path, str(name))
    else:
        out_path = base_path
    if not os.path.exists(out_path):
        os.mkdirs(name)


@delayed
def get_data(argo_file):
    with xr.open_dataset(argo_file) as argo_file:
        argo_file = argo_file.load()
    lats = argo_file.LATITUDE.data
    lons = argo_file.LONGITUDE.data
    depth = argo_file.PRES.data
    new_depth = np.zeros((lats.shape))
    for num, col in enumerate(depth):
        try:
            new_depth[num] = col[~np.isnan(col)][-1]
        except Exception:
            new_depth[num] = -999999
    lons = np.where(lons < 0, lons + 360, lons)
    date = argo_file.JULD.data[0]
    date = np.repeat(pd.to_datetime(date).date(), len(lons))
    nprof = argo_file.N_PROF.data
    platfn = argo_file.PLATFORM_NUMBER.data.astype(int)
    df = {
        "date": date,
        "lat": lats,
        "lon": lons,
        "nprof": nprof,
        "platfn": platfn,
        "depth": new_depth,
        "bio": "N",
    }
    pairs = pd.DataFrame(
        df, columns=["date", "lat", "lon", "nprof", "platfn", "depth", "bio"]
    )
    return pairs


@delayed
def merge_data(list_df):
    return pd.concat(list_df)


def setup_cluster():
    cluster = LocalCluster(n_workers=6, threads_per_worker=1)
    client = Client(cluster)
    return client


def update_data(argo_files, filename="argo_latlon.txt", outdir=os.getcwd()):
    to_update = pd.read_csv(os.path.join(outdir, filename), parse_dates=[0])
    last_date = to_update.iloc[-1]["date"] - pd.DateOffset(60, "D")
    to_update = to_update.drop(to_update[to_update["date"] >= last_date].index)
    to_update = dd.from_pandas(to_update, 10)
    last_date_str = "{:%Y%m%d}".format(last_date)
    ix = [i for i, s in enumerate(argo_files) if last_date_str in s]
    files = argo_files[ix[0] :]
    new_data = merge_data([to_update, merge_data([get_data(argof) for argof in files])])
    return new_data


def check_bio(argo_db):
    print("\nFetching bioARGO data")
    os.system("wget -N ftp://ftp.ifremer.fr/ifremer/argo/argo_merge-profile_index.txt")
    print("Parsing data")
    bio_file = pd.read_csv("argo_merge-profile_index.txt", skiprows=8)
    bio_file["file"] = bio_file["file"].apply(lambda x: int(x.split("/")[1]))
    bio_file = bio_file.loc[:, ["file", "parameters"]]
    mask = bio_file["parameters"].str.contains("DOXY")
    bio_file = bio_file[mask]["file"].unique()
    print("Adding bio flags to output file")
    for afloat in bio_file:
        sel = argo_db.query("platfn==@afloat")
        if not sel.empty:
            argo_db.loc[sel.index, "bio"] = "Y"
    return argo_db


def main(update=False, outdir=os.getcwd(), ARGO_DIR="/data/datos/ARGO/data/"):
    argo_files = [
        os.path.join(ARGO_DIR, x)
        for x in os.listdir(ARGO_DIR)
        if x.endswith("_prof.nc")
    ]
    client = setup_cluster()
    print(client)
    if update:
        updated_data = update_data(argo_files, outdir=outdir)
        updated_data = updated_data.persist()
        progress(updated_data)
        updated_data = check_bio(updated_data.compute().reset_index(drop=True))
        updated_data.to_csv(os.path.join(outdir, "argo_latlon.txt"), index=False)
    else:
        data = merge_data([get_data(argof) for argof in argo_files])
        data = data.persist()
        progress(data)
        data = check_bio(data.compute().reset_index(drop=True))
        data.to_csv(os.path.join(outdir, "argo_latlon.txt"), index=False)


if __name__ == "__main__":
    with open("./../paths.json") as f:
        paths = json.load(f)
    check_folder(paths["ARGO_DB_OUT"])
    main(update=True, outdir=paths["ARGO_DB_OUT"])
