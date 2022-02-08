import datetime
import os

import argopy
import geopandas as gpd
from argopy import IndexFetcher as ArgoIndexFetcher
from dmelon.utils import findPointsInPolys

argopy.set_options(src="localftp", local_ftp="/data/datos/ARGO/gdac")

argopy.set_options(mode="expert")


index_loader = ArgoIndexFetcher()

OUT_PATH = "/data/users/service/ARGO/FLOATS/output/ARGO-plots"


region = [-90, -70, -20, -2.5]
today = datetime.datetime.today()
date_range = [
    f"{today - datetime.timedelta(days=30):%Y-%m-%d}",
    f"{today + datetime.timedelta(days=15):%Y-%m-%d}",
]

argo_df = index_loader.region(region + date_range).to_dataframe().sort_values("date")

mask200 = gpd.read_file("/data/users/grivera/Shapes/NEW_MASK/200mn_full.shp")

pointInPolys = findPointsInPolys(argo_df, mask200)

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from cartopy.io.shapereader import Reader
from dmelon.plotting import format_latlon
from matplotlib.patches import Patch

HQ_BORDER = cfeature.NaturalEarthFeature(
    category="cultural",
    name="admin_0_countries",
    scale="10m",
    facecolor="white",  # cfeature.COLORS['land'],
    edgecolor="black",
    linewidth=1,
)

c50 = "#C8C8C8"
c100 = "#DCDCDC"
c200 = "#F0F0F0"

shape50 = cfeature.ShapelyFeature(
    Reader("/data/users/grivera/Shapes/NEW_MASK/50mn_full.shp").geometries(),
    ccrs.PlateCarree(),
    facecolor=c50,
)

shape100 = cfeature.ShapelyFeature(
    Reader("/data/users/grivera/Shapes/NEW_MASK/100mn_full.shp").geometries(),
    ccrs.PlateCarree(),
    facecolor=c100,
)
shape200 = cfeature.ShapelyFeature(
    Reader("/data/users/grivera/Shapes/NEW_MASK/200mn_full.shp").geometries(),
    ccrs.PlateCarree(),
    facecolor=c200,
)

patch50 = Patch(facecolor=c50, label="0-50nm", edgecolor="gray")
patch100 = Patch(facecolor=c100, label="50-100nm", edgecolor="gray")
patch200 = Patch(facecolor=c200, label="100-200nm", edgecolor="gray")
# patch200 = Patch(facecolor=c200, label="100-200nm", edgecolor="gray")

fig, ax = plt.subplots(
    figsize=(10, 10), dpi=300, subplot_kw=dict(projection=ccrs.PlateCarree())
)

ax.add_feature(HQ_BORDER, zorder=10)
ax.add_feature(shape200)
ax.add_feature(shape100)
ax.add_feature(shape50)
format_latlon(ax, ccrs.PlateCarree(), (-110, -60, -30, 10), 2.5, 2.5)

unique_vals = pointInPolys.sort_values("date").wmo.unique()
for _wmo in (
    pointInPolys.groupby("wmo").nth(-1).sort_values("latitude", ascending=False).index
):
    _sel = pointInPolys.query("wmo==@_wmo")
    ax.plot(_sel.longitude, _sel.latitude, label=_wmo)
    ax.scatter(
        _sel.longitude.iloc[-1],
        _sel.latitude.iloc[-1],
        color="k",
        s=3,
        zorder=9,
    )


ax.set_extent([-85, -70, -20, 0], crs=ccrs.PlateCarree())
ax.grid(ls="--", alpha=0.5)

sca = mlines.Line2D(
    [],
    [],
    color="k",
    marker="o",
    linestyle="none",
    markersize=3,
    label="Latest Position",
)
leg2 = plt.legend(handles=[sca, patch200, patch100, patch50], loc=4)
leg2.set_zorder(100)
ax.add_artist(leg2)

leg = ax.legend(loc=3, title="WMO code")
leg.set_zorder(100)

ax.text(
    0,
    -0.06,
    "Source: ARGO GDAC\nProcessing: IGP",
    transform=ax.transAxes,
    verticalalignment="center",
    horizontalalignment="left",
    fontsize=11,
)

ax.text(
    1,
    -0.06,
    f"Latest date: {pointInPolys.date.max():%b %d %Y}",
    transform=ax.transAxes,
    verticalalignment="center",
    horizontalalignment="right",
    fontsize=11,
)

ax.set_title("ARGO floats within 200nm during the last 30 days")

fig.savefig(os.path.join(OUT_PATH, "CoastMap200nm.png"), bbox_inches="tight")
fig.savefig(os.path.join(OUT_PATH, "CoastMap200nm.jpeg"), bbox_inches="tight", dpi=200)
