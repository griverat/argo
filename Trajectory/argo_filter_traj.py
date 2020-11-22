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
import geopandas as gpd
from shapely.geometry import Point
from geopandas.tools import sjoin

# from send_email import send_mail
import pandas as pd
import argparse
import json
import os

with open("./../paths.json") as f:
    paths = json.load(f)
out_plot = paths["TRAJ_PLOT_OUT"]


def filter_date(prof, argo_db, days):
    delta = pd.Timedelta(days, "D")
    argo_db = argo_db.query("(platfn==@prof)")
    today = argo_db.date.iloc[-1]
    st_date = today - delta
    filtered = argo_db.query("date>=@st_date").reset_index(drop=True)[
        ["date", "lat", "lon"]
    ]
    return filtered


def build_ts(end_date, tbefore, days):
    delta = pd.Timedelta(days, "D")
    tbefore = pd.Timedelta(tbefore, "D")
    lim_date = end_date - tbefore
    new_time = end_date
    date_lims = []
    date_lims.append(new_time)
    while new_time >= lim_date:
        new_time -= delta
        date_lims.append(new_time)
    return date_lims


def group_dates(filter_db, day_thres):
    today = pd.to_datetime(
        datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    date_ranges = build_ts(today, 365, 30)
    for i in range(len(date_ranges)):
        dbefore = date_ranges[i]
        try:
            dafter = date_ranges[i + 1]
            ix_ = filter_db.query("(date<=@dbefore)&(date>@dafter)").index
        except Exception:
            print("Reached final date")
            ix_ = filter_db.query("date<@dbefore").index

        for ix in ix_:
            filter_db.loc[ix, "class"] = i
    return filter_db


def check_update(old_file, new_date):
    try:
        old_data = pd.read_csv(old_file, sep=" ", parse_dates=[0])
    except Exception:
        print("Old file not found.\nCreating file")
        return True
    old_date = old_data.iloc[-1, 0]
    if old_date == new_date:
        print("No new data found")
        return False
    else:
        print("New data found")
        return True


def get_gr(orig_date):
    return "{:%d%b%Y}".format(orig_date)


def launch_grads(profcode, lats, lons):
    os.chdir(paths["TRAJ_PLOT_DIR"])
    args = "{} {} {} {} {}".format(*lats, *lons, paths["ARGO_PROF_OUT"])
    os.system(f'grads -d X11 -blc "run plot_map_func.gs {profcode} {args}"')
    os.chdir(paths["TRAJ_DIR"])

    os.system(f"sh convert_eps.sh '{out_plot}/{profcode}/*.eps'")


def inreg_db(argo_db):
    crs = {"init": "epsg:4326"}
    fix_lon = argo_db.copy()
    fix_lon["lon"] = fix_lon["lon"].apply(lambda x: x - 360 if x > 180 else x)
    geometry = [Point(xy) for xy in zip(fix_lon["lon"], fix_lon["lat"])]
    starts = gpd.GeoDataFrame(fix_lon, crs=crs, geometry=geometry)

    SA_200 = gpd.read_file("/data/users/grivera/Shapes/costa_200mn_mask.shp")
    SA_100 = gpd.read_file("/data/users/grivera/Shapes/costa_100mn_mask.shp")
    SA_50 = gpd.read_file("/data/users/grivera/Shapes/costa_50mn_mask.shp")
    #     SA_300['geometry'] = SA_300.geometry.buffer(1)
    pointIn200 = sjoin(starts, SA_200, how="left", op="within")
    pointIn200 = pointIn200.dropna()
    pointIn100 = sjoin(starts, SA_100, how="left", op="within")
    pointIn100 = pointIn100.dropna()
    pointIn50 = sjoin(starts, SA_50, how="left", op="within")
    pointIn50 = pointIn50.dropna()

    argo_db["in200"] = "0"
    argo_db["in100"] = "0"
    argo_db["in50"] = "0"

    argo_db.loc[pointIn200.index, "in200"] = "1"
    argo_db.loc[pointIn100.index, "in100"] = "1"
    argo_db.loc[pointIn50.index, "in50"] = "1"
    return argo_db


def filter_traj(prof_num, argo_db):
    argo_filter = filter_date(prof_num, argo_db, 365)
    argo_filter = group_dates(argo_filter, 30)
    argo_filter.loc[:, "GrADS"] = argo_filter["date"].apply(get_gr)
    argo_filter = inreg_db(argo_filter)
    lat_mean, lon_mean = (
        argo_filter.min()[["lat", "lon"]] + argo_filter.max()[["lat", "lon"]]
    ) / 2
    filename = os.path.join(paths["ARGO_PROF_OUT"], "{}-traj{}.txt")
    if check_update(filename.format(prof_num, 1), argo_filter.date.iloc[-1]):
        for i in range(1, 6):
            argo_filter.to_csv(
                filename.format(prof_num, i),
                header=None,
                index=None,
                sep=" ",
                float_format="%.5f",
            )
        return True, (lat_mean, lon_mean)
    else:
        return False, None


def check_folder(base_path, name=None):
    if name is not None:
        out_path = os.path.join(base_path, str(name))
    else:
        out_path = base_path
    if not os.path.exists(out_path):
        os.makedirs(out_path)


def main(prof_num):
    argo_db = pd.read_csv(paths["ARGO_DB"], parse_dates=[0])
    argo_db = argo_db.sort_values("date").reset_index(drop=True)

    update, mcenter = filter_traj(prof_num, argo_db)
    if update:
        map_bounds = {
            "lats": (mcenter[0] - 3.5, mcenter[0] + 3.5),
            "lons": (mcenter[1] - 3.5, mcenter[1] + 3.5),
        }
        check_folder(out_plot, prof_num)
        launch_grads(prof_num, map_bounds["lats"], map_bounds["lons"])
        # send_mail(prof_num)


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description="Plot the last year of data and position of an ARGO float"
    )
    parser.add_argument("profnum", type=int, help="ARGO float id")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = getArgs()
    print(args.profnum)
    main(args.profnum)
