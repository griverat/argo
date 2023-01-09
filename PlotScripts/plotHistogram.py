import datetime
import os

import argopy
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher
from geopandas.tools import sjoin

argopy.set_options(src="gdac", ftp="/data/datos/ARGO/gdac")

argopy.set_options(mode="expert")

argo_loader = ArgoDataFetcher(parallel=True, progress=True)

index_loader = ArgoIndexFetcher()

region = [-110, -65, -60, 5]
OUT_PATH = "/data/users/service/ARGO/FLOATS/output/ARGO-plots"

argo_df = index_loader.region(region).to_dataframe().sort_values("date")

cars_o2 = (
    xr.open_dataset("/data/datos/CARS2009/CARS2009/o2_ann.cdf")
    .rename(X="lon", Y="lat", Z="level")
    .oxygen
)

scaled_o2 = cars_o2 / 44.64

from sklearn.neighbors import KernelDensity

lats = (-60, 5)
lons = (-110, -65)
bin_size = 0.5
x_grid = np.arange(lons[0], lons[1] + 0.1, bin_size)
y_grid = np.arange(lats[0], lats[1] + 0.1, bin_size)
H, xedges, yedges = np.histogram2d(
    argo_df["longitude"],
    argo_df["latitude"],
    bins=(x_grid, y_grid),
)
H = H.T
X, Y = np.meshgrid(xedges, yedges)

bw = 1.2
x = argo_df["longitude"].values
y = argo_df["latitude"].values
k = KernelDensity(kernel="gaussian", bandwidth=bw).fit(np.vstack([x, y]).T)
xi, yi = np.mgrid[
    x.min() : x.max() : H.shape[1] * 1j,
    y.min() : y.max() : H.shape[0] * 1j,
]
zi = np.exp(k.score_samples(np.vstack([xi.ravel(), yi.ravel()]).T))

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from dmelon.plotting import format_latlon


def add_patch(ax, region, kwargs={}):
    ax.add_patch(
        mpatches.Rectangle(
            xy=[region[1][0], region[0][0]],
            width=region[1][1] - region[1][0],
            height=region[0][1] - region[0][0],
            transform=ccrs.PlateCarree(),
            zorder=30,
            **kwargs,
        )
    )


HQ_BORDER = cfeature.NaturalEarthFeature(
    category="cultural",
    name="admin_0_countries",
    scale="50m",
    facecolor=cfeature.COLORS["land"],
    edgecolor="black",
    linewidth=0.5,
)

bmax = 100
bint = 10
boundaries = np.arange(0, bmax + 1, bint)
nlevs = 10


cmap_reds = plt.cm.get_cmap("Blues", len(boundaries))
colors = list(cmap_reds(np.arange(len(boundaries))))
colors[0] = "white"
cmap = mpl.colors.ListedColormap(colors[:-1], "")
cmap.set_over(colors[-1])

fig, ax = plt.subplots(
    subplot_kw=dict(projection=ccrs.PlateCarree()), figsize=(24, 12), dpi=400
)
ax.add_feature(HQ_BORDER, zorder=5)
format_latlon(ax, ccrs.PlateCarree(), [-120, -60, -80, 10], 5, 5)

draw = ax.pcolormesh(
    X,
    Y,
    H,
    edgecolor="w",
    lw=0.004,
    transform=ccrs.PlateCarree(),
    cmap=cmap,
    norm=mpl.colors.BoundaryNorm(boundaries, ncolors=len(boundaries) - 1),
)


ax.contour(
    xi,
    yi,
    zi.reshape(xi.shape),
    levels=np.linspace(0, zi.max(), nlevs + 1),
    transform=ccrs.PlateCarree(),
    cmap=plt.get_cmap("pink_r", nlevs),
    linewidths=np.linspace(0, 3, nlevs + 1),
)

cmap = plt.get_cmap("pink_r", 8)
cmaplist = [cmap(i) for i in range(cmap.N)]
for j in range(len(cmaplist)):
    cmaplist[j] = (1.0, 1.0, 1.0, 0)
cmap = cmap.from_list("Custom cmap", cmaplist, cmap.N)

ax.contourf(
    xi,
    yi,
    zi.reshape(xi.shape),
    transform=ccrs.PlateCarree(),
    cmap=cmap,
    hatches=[None] * (nlevs - 3) + ["\\\\", "//", "--"],
    levels=np.linspace(0, zi.max(), nlevs + 1),
)

cbar_kwargs = {"orientation": "horizontal", "drawedges": True}
cbar_axes = [0.39, 0.16, 0.105, 0.01]

cbaxes = fig.add_axes(cbar_axes)
plt.colorbar(draw, cax=cbaxes, ticks=boundaries, extend="max", **cbar_kwargs)

scaled_o2.sel(level=300, method="nearest").sel(
    lat=slice(-60, 5), lon=slice(-110, -65)
).plot.contour(ax=ax, levels=[1], colors="r")


red_line = mlines.Line2D([], [], color="red", label="$1mL/L$ at 300m depth")

ax.legend(handles=[red_line])

kwargs = {"fill": False, "edgecolor": "black", "linewidth": 2, "ls": "--"}
bbox = dict(boxstyle="round", facecolor="white", pad=0.2, alpha=0.5)
add_patch(ax, [(-1.5, 2.5), (252.5, 259)], kwargs=kwargs)
add_patch(ax, [(-22, -16), (272.5, 280)], kwargs=kwargs)
ax.annotate(
    "Zone 2", xy=(-86.5, -23.8), bbox=bbox, size=15, transform=ccrs.PlateCarree()
)
ax.annotate("Zone 1", xy=(-107, -3.4), bbox=bbox, size=15, transform=ccrs.PlateCarree())

ax.set_title(
    f"ARGO data histogram and density contours over 1981-{argo_df.date.max():%Y}",
    pad=10,
)

ax.set_extent(region, crs=ccrs.PlateCarree())

fig.savefig(os.path.join(OUT_PATH, "HistKdeOMZ_argo.png"), bbox_inches="tight")
fig.savefig(
    os.path.join(OUT_PATH, "HistKdeOMZ_argo.jpeg"), bbox_inches="tight", dpi=200
)
