#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Sun Aug 11 01:00:41 2019
Author: Gerardo A. Rivera Tello
Email: gerardo_art@me.com
-----
"""

import pandas as pd
import numpy as np
import json
import argparse
import datetime
import os

import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as mpatches
import matplotlib.cm as cmx
import cartopy.feature as cfeature

with open("./../paths.json") as f:
    paths = json.load(f)

plt.style.use("seaborn-paper")


def check_folder(base_path, name=None):
    if name is not None:
        out_path = os.path.join(base_path, str(name))
    else:
        out_path = base_path
    if not os.path.exists(out_path):
        os.makedirs(out_path)


class Argo_plot(object):
    def __init__(self, plons, plats):
        self.proj = ccrs.PlateCarree(central_longitude=180)
        self.fig, self.ax = plt.subplots(
            subplot_kw=dict(projection=self.proj), figsize=(24, 12), dpi=400
        )
        self.ax.set_xticks(np.arange(0, 360, 2.5), crs=ccrs.PlateCarree())
        self.ax.set_yticks(np.arange(-90, 90, 2.5), crs=ccrs.PlateCarree())
        lon_formatter = LongitudeFormatter(zero_direction_label=True)
        lat_formatter = LatitudeFormatter()
        self.ax.xaxis.set_major_formatter(lon_formatter)
        self.ax.yaxis.set_major_formatter(lat_formatter)
        self.ax.grid(alpha=0.5, ls="--")
        hq_border = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_0_countries",
            scale="10m",
            facecolor="white",  # cfeature.COLORS['land'],
            edgecolor="black",
            linewidth=1.5,
        )
        self.ax.add_feature(hq_border)
        plons = tuple(plon - 180 for plon in plons)
        self.ax.set_extent([*plons, *plats], crs=self.proj)
        self.ax.tick_params(labelsize=15)

    def set_colormap(self, num):
        hot = plt.get_cmap("nipy_spectral")
        cNorm = colors.Normalize(vmin=0, vmax=num)
        self.scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=hot)

    def add_patch(self, regions):
        for region in regions:
            rect = mpatches.Rectangle(
                xy=[region[1][0], region[0][0]],
                width=region[1][1] - region[1][0],
                height=region[0][1] - region[0][0],
                facecolor="black",
                alpha=0.1,
                transform=ccrs.PlateCarree(),
            )
            self.ax.add_patch(rect)

    def plot_data(self, data, title):
        uniq = data["date"].unique()
        tod = pd.to_datetime(datetime.date.today())
        for num, adate in enumerate(uniq):
            adate = pd.to_datetime(adate)
            tdiff = tod - adate
            if (tdiff <= np.timedelta64(6, "D")) and (tdiff > np.timedelta64(3, "D")):
                mar = "P"
            elif tdiff <= np.timedelta64(3, "D"):
                mar = "H"
            else:
                mar = "X"
            plot_data = data.query("date==@adate")
            self.ax.scatter(
                plot_data["lon"],
                plot_data["lat"],
                s=(np.abs(2 + num)) * 50,
                marker=mar,
                alpha=0.8,
                color=self.scalarMap.to_rgba(9 - tdiff.days),
                edgecolor="k",
                lw=1,
                transform=ccrs.PlateCarree(),
                label="{:%Y-%m-%d}".format(adate),
                zorder=num + 1,
            )
        leg = self.ax.legend(
            loc=3, fontsize="x-large", frameon=True, fancybox=True, edgecolor="k"
        )
        leg.set_title(title, prop={"size": "x-large"})
        plt.gca().add_artist(leg)

    def save_fig(self, name):
        eps = "{}.eps".format(name)
        png = "{}.png".format(name)
        jpg = "{}.jpg".format(name)
        self.fig.savefig(png, bbox_inches="tight")
        self.fig.savefig(eps, bbox_inches="tight")
        self.fig.savefig(jpg, dpi=60, bbox_inches="tight")


def filter_db(database, days_before, reglist):
    today = np.datetime64(datetime.date.today())
    delta = np.timedelta64(days_before, "D")
    dataf = pd.DataFrame([])
    for region in reglist:
        lats, lons = region
        floats_reg = database.query(
            "(lat>={})&(lat<={})&(lon>={})&(lon<={})".format(*lats, *lons)
        )
        data = floats_reg.iloc[np.where(today - floats_reg["date"] < delta)]
        dataf = pd.concat([dataf, data]).sort_values("date").reset_index(drop=True)
    return dataf


def list_of_tuples(arg):
    return [tuple(map(float, x.split(","))) for x in arg.split(";")]


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description="Plot the location of the ARGO profilers inside an specified region \
                    over the last specified dates"
    )
    parser.add_argument("days", type=int, help="Days before today to look")
    parser.add_argument("name", type=str, help="Name of the output file")
    parser.add_argument(
        "--reg_list",
        type=list_of_tuples,
        action="append",
        help="Boundaries of the patch as lat1,lat2;lon1,lon2",
    )
    parser.add_argument(
        "--plat", type=float, nargs=2, help="Lat boundaries of the displayed map"
    )
    parser.add_argument(
        "--plon", type=float, nargs=2, help="Lon boundaries of the displayed map"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    ARGODB = paths["ARGO_DB"]
    TRACKER_OUT = paths["TRACKER_OUT"]
    check_folder(TRACKER_OUT)
    argo_db = (
        pd.read_csv(ARGODB, parse_dates=[0]).sort_values("date").reset_index(drop=True)
    )

    args = getArgs()
    print(args.reg_list)
    Argo_plot = Argo_plot(args.plon, args.plat)
    Argo_plot.set_colormap(args.days)
    Argo_plot.add_patch(args.reg_list)

    dataf = filter_db(argo_db, args.days, args.reg_list)

    Argo_plot.plot_data(dataf, "Fecha")
    Argo_plot.save_fig(os.path.join(TRACKER_OUT, f"argo_tracker_{args.name}"))
