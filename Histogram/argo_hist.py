#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Thu Jan 31 09:55:53 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2018 Instituto Geofisico del Peru
-----
"""

from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from scipy.stats.kde import gaussian_kde
from sklearn.neighbors.kde import KernelDensity
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
import os


class ArgoHist(object):
    def __init__(self):
        self.proj = ccrs.PlateCarree(central_longitude=180)

    def load_data(self, data):
        self.data = data

    def filter_data(self, dates, lats, lons, bin_size=0.5, val=None):
        self.dates = [
            pd.to_datetime(date) if not isinstance(date, pd.datetime) else date
            for date in dates
        ]
        self.x_grid = np.arange(lons[0], lons[1] + 0.1, bin_size)
        self.y_grid = np.arange(lats[0], lats[1] + 0.1, bin_size)
        self.filt_data = filter_data(self.data, *lats, *lons, *self.dates, val)

    def get_histogram(self):
        H, xedges, yedges = np.histogram2d(
            self.filt_data["lon"],
            self.filt_data["lat"],
            bins=(self.x_grid, self.y_grid),
        )
        self.H = H.T
        self.X, self.Y = np.meshgrid(xedges, yedges)

    def get_kde(self):
        x = self.filt_data["lon"].values
        y = self.filt_data["lat"].values
        k = gaussian_kde(np.vstack([x, y]))
        self.xi, self.yi = np.mgrid[
            x.min() : x.max() : self.H.shape[1] * 1j,
            y.min() : y.max() : self.H.shape[0] * 1j,
        ]
        self.zi = k(np.vstack([self.xi.flatten(), self.yi.flatten()]))

    def get_kde_scipy(self, bw=1.5):
        x = self.filt_data["lon"].values
        y = self.filt_data["lat"].values
        k = KernelDensity(kernel="gaussian", bandwidth=bw).fit(np.vstack([x, y]).T)
        self.xi, self.yi = np.mgrid[
            x.min() : x.max() : self.H.shape[1] * 1j,
            y.min() : y.max() : self.H.shape[0] * 1j,
        ]
        self.zi = np.exp(
            k.score_samples(np.vstack([self.xi.ravel(), self.yi.ravel()]).T)
        )

    def setup_plot(self, lat1, lat2, lon1, lon2):
        plt.style.use("seaborn-paper")
        self.fig, self.ax = plt.subplots(
            subplot_kw=dict(projection=self.proj), figsize=(24, 12), dpi=400
        )
        self.ax.set_xticks(np.arange(0, 360, 5), crs=ccrs.PlateCarree())
        self.ax.set_yticks(np.arange(-90, 90, 2.5), crs=ccrs.PlateCarree())
        lon_formatter = LongitudeFormatter(zero_direction_label=True)
        lat_formatter = LatitudeFormatter()
        self.ax.xaxis.set_major_formatter(lon_formatter)
        self.ax.yaxis.set_major_formatter(lat_formatter)
        self.ax.set_extent([lon1 + 180, lon2 + 180, lat1, lat2], crs=self.proj)
        hq_border = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_0_countries",
            scale="50m",
            facecolor=cfeature.COLORS["land"],
            edgecolor="black",
        )
        self.ax.add_feature(hq_border, zorder=5)
        self.ax.tick_params(labelsize=5)

    def custom_cmap(self):
        cmap = plt.get_cmap("pink_r", 8)
        cmaplist = [cmap(i) for i in range(cmap.N)]
        for j in range(len(cmaplist)):
            cmaplist[j] = (1.0, 1.0, 1.0, 0)
        cmap = cmap.from_list("Custom cmap", cmaplist, cmap.N)
        return cmap

    def plot(
        self,
        plats,
        plons,
        bmax=50,
        bint=10,
        nlevs=8,
        contours=True,
        cbar_kwargs={},
        cbar_axes=[],
    ):
        self.setup_plot(*plats, *plons)
        boundaries = np.arange(0, bmax + 1, bint)
        cmap_reds = plt.cm.get_cmap("Blues", len(boundaries))
        colors = list(cmap_reds(np.arange(len(boundaries))))
        colors[0] = "white"
        cmap = mpl.colors.ListedColormap(colors[:-1], "")
        cmap.set_over(colors[-1])

        draw = self.ax.pcolormesh(
            self.X,
            self.Y,
            self.H,
            edgecolor="w",
            lw=0.004,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            vmin=0,
            vmax=bmax,
            norm=mpl.colors.BoundaryNorm(boundaries, ncolors=len(boundaries) - 1),
        )
        if contours:
            self.ax.contour(
                self.xi,
                self.yi,
                self.zi.reshape(self.xi.shape),
                levels=np.linspace(0, self.zi.max(), nlevs + 1),
                transform=ccrs.PlateCarree(),
                cmap=plt.get_cmap("pink_r", nlevs),
                linewidths=np.linspace(0, 3, nlevs + 1),
            )
            cmap = self.custom_cmap()
            cs = self.ax.contourf(
                self.xi,
                self.yi,
                self.zi.reshape(self.xi.shape),
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                hatches=[None] * (nlevs - 3) + ["\\\\", "//", "--"],
                levels=np.linspace(0, self.zi.max(), nlevs + 1),
            )
        cbaxes = self.fig.add_axes(cbar_axes)
        plt.colorbar(draw, cax=cbaxes, ticks=boundaries, extend="max", **cbar_kwargs)

        self.ax.tick_params(labelsize="medium")

    def add_patch(self, region, kwargs={}):
        self.ax.add_patch(
            mpatches.Rectangle(
                xy=[region[1][0], region[0][0]],
                width=region[1][1] - region[1][0],
                height=region[0][1] - region[0][0],
                transform=ccrs.PlateCarree(),
                zorder=30,
                **kwargs
            )
        )

    def show(self, output, batch):
        if not batch:
            plt.show()
        self.fig.savefig(os.path.join(output, "hist+kde_argo.eps"), bbox_inches="tight")
        self.fig.savefig(os.path.join(output, "hist+kde_argo.png"), bbox_inches="tight")


def load_data(filename):
    data = (
        pd.read_csv(filename, parse_dates=[0])
        .sort_values("date")
        .reset_index(drop=True)
        .set_index("platfn")
    )
    return data


def filter_data(data, min_lat, max_lat, min_lon, max_lon, time1, time2, val=None):
    data = data.query("(date>@time1)&(date<=@time2)")
    if val is not None:
        filt = []
        for number in data.index.unique():
            traj_data = data.query("platfn==@number").sort_values(by="date")
            if val == "first":
                _val = traj_data.iloc[0]
            if val == "last":
                _val = traj_data.iloc[-1]
            if (
                (_val.lat > min_lat)
                & (_val.lat < max_lat)
                & (_val.lon > min_lon)
                & (_val.lon < max_lon)
            ):
                filt.append(_val)
        filt = pd.DataFrame(filt)
    else:
        filt = data.query("(lat>@min_lat)&(lat<@max_lat)&(lon>@min_lon)&(lon<@max_lon)")
    return filt


if __name__ == "__main__":
    dates = ("1999-01-01", "2019-12-31")
    lats = (-60, 5)
    lons = (250, 290)
    data = load_data("/data/users/grivera/ARGO-latlon/argo_latlon.txt")
    pcoords = ([-60, 5], [250, 295])

    Hist = ArgoHist()
    Hist.load_data(data)

    Hist.filter_data(dates, lats, lons, bin_size=0.5)
    Hist.get_histogram()
    Hist.get_kde_scipy(bw=1.2)

    Hist.plot(
        *pcoords,
        bmax=100,
        bint=10,
        contours=True,
        nlevs=10,
        cbar_kwargs={"orientation": "horizontal", "drawedges": True},
        cbar_axes=[0.39, 0.15, 0.085, 0.01]
    )
    kwargs = {"fill": False, "edgecolor": "black", "linewidth": 2, "ls": "--"}
    bbox = dict(boxstyle="round", facecolor="white", pad=0.2)

    Hist.ax.annotate("Zone 2", xy=(94, -23.8), bbox=bbox, size=15)
    Hist.ax.annotate("Zone 1", xy=(73.2, -3.4), bbox=bbox, size=15)

    Hist.add_patch([(-1.5, 2.5), (252.5, 259)], kwargs=kwargs)
    Hist.add_patch([(-22, -16), (272.5, 280)], kwargs=kwargs)
    Hist.show("/home/grivera/GitLab/argo/Histogram/Output", True)
