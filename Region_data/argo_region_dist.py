#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Mon Feb 18 03:08:07 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2018 Instituto Geofisico del Peru
-----
"""

from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as mpatches
import matplotlib.cm as cmx
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
import xarray as xr
import itertools
import datetime
import time
import os


class DistPlot(object):
    def __init__(self, data):
        plt.style.use("seaborn-paper")
        self.data = data
        self.proj = ccrs.PlateCarree(central_longitude=180)
        self.fig, self.ax = plt.subplots(
            subplot_kw=dict(projection=self.proj), figsize=(24, 12)
        )
        self.ax.set_xticks(np.arange(0, 360, 2.5), crs=ccrs.PlateCarree())
        self.ax.set_yticks(np.arange(-90, 90, 2.5), crs=ccrs.PlateCarree())
        lon_formatter = LongitudeFormatter(zero_direction_label=True)
        lat_formatter = LatitudeFormatter()
        self.ax.xaxis.set_major_formatter(lon_formatter)
        self.ax.yaxis.set_major_formatter(lat_formatter)

    def plot(self, plats, plons, lats, lons):
        self.ax.add_patch(
            mpatches.Rectangle(
                xy=[lons[0], lats[0]],
                width=lons[1] - lons[0],
                height=lats[1] - lats[0],
                facecolor="black",
                alpha=0.1,
                transform=ccrs.PlateCarree(),
                zorder=0,
            )
        )
        self.ax.grid(alpha=0.5, ls="--")

        hq_border = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_0_countries",
            scale="50m",
            facecolor=cfeature.COLORS["land"],
            edgecolor="black",
        )
        self.ax.add_feature(hq_border)
        self.ax.set_extent([plons[0], plons[1], plats[0], plats[1]], crs=self.proj)

        uniq = list(set(self.data.date))
        uniq.sort()
        clmap = plt.get_cmap("hot")
        cNorm = colors.Normalize(vmin=0, vmax=len(uniq))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=clmap)

        # marker = itertools.cycle(('P', 'X', 'H', 'v', 'd', 's', 'o', '*'))
        marker = itertools.cycle([(i + 3, 0, i * 60) for i in range(4)] * len(uniq))
        for i in range(len(uniq)):
            indx = self.data.date == uniq[i]
            if (i < 4) & (i >= 1):
                mar = "P"
            elif i < 1:
                mar = "X"
            else:
                mar = "H"
            self.ax.scatter(
                self.data["lon"][indx],
                self.data["lat"][indx],
                s=(i + 6) ** 2.2,
                marker=next(marker),
                alpha=0.8,
                color=scalarMap.to_rgba(i),
                edgecolor="k",
                lw=1,
                transform=ccrs.PlateCarree(),
                label=uniq[i].date(),
            )

        self.ax.legend(fontsize="x-large", frameon=True, fancybox=True, edgecolor="k")
        # ax.gridlines(crs=ccrs.PlateCarree(), linewidth=2, color='black', alpha=0.5, linestyle='--', draw_labels=False)
        # cbar = plt.colorbar(draw, ticks = np.arange(np.min(H),np.max(H),10))
        # cbar.ax.tick_params(labelsize=15)  ro, nara, amaril ,cel ,azul
        # fig.savefig('/home/grivera/GitLab/argo/Notebooks/Output/last10days_argo.png',dpi=400,bbox_inches='tight')

    def show(self):
        plt.show()


def read_argodb(dbdir):
    argodb = pd.read_csv(os.path.join(dbdir, "argo_latlon.txt"), parse_dates=[0])
    return argodb


def filter_data(argodb, lat, lon, tdelta=10, tdate=False):
    if tdate is False:
        delta = np.timedelta64(tdelta, "D")
        filt = argodb.iloc[
            np.where(np.datetime64(datetime.date.today()) - argodb.date < delta)
        ]
    else:
        filt = argodb[(argodb["date"] > tdate[0]) & (argodb["date"] < tdate[1])]
    filt = filt[(filt["lat"] >= lat[0]) & (filt["lat"] <= lat[1])]
    filt = filt[(filt["lon"] >= lon[0]) & (filt["lon"] <= lon[1])]
    return filt


def main(plats, plons, lats, lons, ARGODB_DIR="/data/users/grivera/ARGO-latlon"):
    argodb = read_argodb(ARGODB_DIR)
    argodb = filter_data(argodb, lats, lons, tdate=["2019-02-01", "2019-02-21"])
    region_dist = DistPlot(argodb)
    region_dist.plot(plats, plons, lats, lons)
    region_dist.show()


if __name__ == "__main__":
    main([-20, 10], [70, 110], [-2.5, 2.5], [253, 260])
