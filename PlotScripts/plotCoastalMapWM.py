import datetime
import os

import argopy
import geopandas as gpd
import gsw
import numpy as np
import pandas as pd
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher
from dmelon.utils import findPointsInPolys
from scipy import interpolate

argopy.set_options(src="gdac", ftp="/data/datos/ARGO/gdac")

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


argo_codes = (
    pointInPolys.sort_values("date")
    .groupby("wmo")
    .nth(-1)
    .sort_values("latitude", ascending=False)
    .index.tolist()
)
print(argo_codes)

argo_loader = ArgoDataFetcher(parallel=True, progress=True)

ds = argo_loader.float(argo_codes).to_xarray()
ds_profile = ds.argo.point2profile().sortby("TIME")

ds_profile_qc = ds_profile.copy()
ds_profile_qc["PSAL"] = ds_profile.PSAL.where(ds_profile.PSAL_QC == 1)
ds_profile_qc["TEMP"] = ds_profile.TEMP.where(ds_profile.TEMP_QC == 1)
ds_profile_qc["PRES"] = ds_profile.PRES.where(ds_profile.PRES_QC == 1)


level = np.arange(0, 2100, 1)

_float_cont = []

for argo_code in argo_codes:

    _argo_profile = ds_profile_qc.where(ds_profile.PLATFORM_NUMBER == argo_code).dropna(
        dim="N_PROF", how="all"
    )
    sdate = pd.to_datetime(date_range[0])

    _argo_profile = _argo_profile.where(ds_profile.TIME > sdate).dropna(
        dim="N_PROF", how="all"
    )

    _cont = []

    for _prof_num in _argo_profile.N_PROF.data:
        _sel_prof = _argo_profile.sel(N_PROF=_prof_num)
        _non_nan_index = _sel_prof.PRES.dropna("N_LEVELS").N_LEVELS
        _PRES = _sel_prof.PRES.sel(N_LEVELS=_non_nan_index).data
        _TEMP = _sel_prof.TEMP.sel(N_LEVELS=_non_nan_index).data
        _PSAL = _sel_prof.PSAL.sel(N_LEVELS=_non_nan_index).data

        if _PRES.size == 0:
            continue

        if _PRES[0] < 10:
            _PRES = np.concatenate(([0], _PRES))
            _TEMP = np.concatenate((_TEMP[[0]], _TEMP))
            _PSAL = np.concatenate((_PSAL[[0]], _PSAL))
        _LEVEL = gsw.z_from_p(_PRES, np.full_like(_PRES, _sel_prof.LATITUDE.data)) * -1
        TEMP_func = interpolate.interp1d(_LEVEL, _TEMP, bounds_error=False)
        PSAL_func = interpolate.interp1d(_LEVEL, _PSAL, bounds_error=False)
        TEMP_interp = TEMP_func(level)
        PSAL_interp = PSAL_func(level)

        _interp = xr.Dataset(
            data_vars=dict(
                TEMP=(["level"], TEMP_interp),
                PSAL=(["level"], PSAL_interp),
            ),
            coords=dict(level=(["level"], level), TIME=_sel_prof.TIME, pcode=argo_code),
        )
        _cont.append(_interp)
    _float_cont.append(xr.concat(_cont, dim="TIME").interpolate_na(dim="level").load())

float_cont = xr.concat(_float_cont, dim="pcode").sortby("TIME")

################################################

from typing import NamedTuple, Optional, Union


class WMthresh(NamedTuple):
    min_temp: Union[float, None]
    max_temp: Union[float, None]
    min_psal: Union[float, None]
    max_psal: Union[float, None]
    max_levl: Optional[float] = None


DEF_MIN = -999
DEF_MAX = 999

classification = {
    "ZutaGuillen": {
        "TSW": WMthresh(DEF_MIN, DEF_MAX, DEF_MIN, 33.8, 100),
        "ESW": WMthresh(DEF_MIN, DEF_MAX, 33.8, 34.8, 100),
        "STSW": WMthresh(DEF_MIN, DEF_MAX, 35.1, DEF_MAX, 100),
        "CCW": WMthresh(DEF_MIN, DEF_MAX, 34.8, 35.1, 100),
        "ESSW": WMthresh(13, 15, 34.9, 35.1),
        "ESPIW": WMthresh(13, 15, 34.6, 34.8),
        "DESSW": WMthresh(7, 13, 34.6, 34.9),
        "AAIW": WMthresh(4, 7, 34.45, 34.6),
    },
    "Carmen": {
        "TSW": WMthresh(23.5, 24.5, 33.5, 34.4),
        # "CCW": WMthresh(DEF_MIN, DEF_MAX, 34.8, 35.1, 100),
        "PCW": WMthresh(15, 18.5, 34.8, 35.2),
        "ESW": WMthresh(20, 24, 34.6, 35),
        "STSW": WMthresh(19, 23.5, 35.4, DEF_MAX),
        "ESSW": WMthresh(8, 14, 34.6, 35),
        "ESPIW": WMthresh(12, 14, 34.8, 34.8),
        "AAIW": WMthresh(4, 7, 34.5, 34.6),
    },
}

locale = {
    "TSW": "Tropical Surface Water",
    "ESW": "Equatorial Surface Water",
    "STSW": "SubTropical Surface Water",
    "CCW": "Cold Coastal Water",
    "ESSW": "Equatorial SubSurface Water",
    "ESPIW": "Eastern South Pacific Intermediate Water",
    "DESSW": "Deep Equatorial SubSurface Water",
    "AAIW": "Antartic Intermediate Water",
}

classification_colors = {
    "ZutaGuillen": [
        "navy",
        "royalblue",
        "slateblue",
        "cornflowerblue",
        "cyan",
        "goldenrod",
        "coral",
        "firebrick",
    ],
    "Carmen": [
        "navy",
        "slateblue",
        "cornflowerblue",
        # "lightsteelblue",
        # "lightseagreen",
        "goldenrod",
        "coral",
        "cyan",
        "firebrick",
    ],
}


def waterMass(temperature, salinity, criterion="ZutaGuillen"):
    crit = classification[criterion]
    out = {}
    for num, (water_mass, ranges) in enumerate(crit.items()):
        _temp = xr.full_like(temperature, num, dtype=float)
        # Using temperature
        _temp = _temp.where(temperature > ranges.min_temp).where(
            temperature < ranges.max_temp
        )

        # Using salinity
        if ranges.min_psal == ranges.max_psal:
            _temp = _temp.where(salinity == ranges.min_psal)
        else:
            _temp = _temp.where(salinity > ranges.min_psal).where(
                salinity < ranges.max_psal
            )
        if ranges.max_levl is not None and "level" in _temp.dims:
            _temp = _temp.where(_temp.level < ranges.max_levl)
        out[water_mass] = _temp
    return out


################################################

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import gsw
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from cartopy.io.shapereader import Reader
from dmelon.plotting import format_latlon
from matplotlib import colors
from matplotlib.patches import Patch
from shapely.geometry import LineString, Point

peru_line = gpd.read_file(
    "/data/users/grivera/Shapes/ESRI/baseline_diss_lines.shp", crs="EPSG:4326"
)


def redistribute_vertices(geom, distance, xarr):
    if geom.geom_type == "LineString":
        num_vert = int(round(geom.length / distance))
        if num_vert == 0:
            num_vert = 1
        points = [
            geom.interpolate(float(n) / num_vert, normalized=True)
            for n in range(num_vert + 1)
        ]
        points = [
            Point(point.x - xarr.sel(lat=point.y, method="nearest").data, point.y)
            for point in points
        ]
        return LineString(points)
    elif geom.geom_type == "MultiLineString":
        parts = [redistribute_vertices(part, distance, xarr) for part in geom.geoms]
        return type(geom)([p for p in parts if not p.is_empty])
    else:
        raise ValueError("unhandled geometry %s", (geom.geom_type,))


lamb = (
    3
    * np.abs(
        gsw.geostrophy.f(
            xr.DataArray(np.nan, coords=[("lat", np.arange(0, -20, -0.1))]).lat
        )
    )
    ** -1
)
lamb = lamb / 111e3

ross = peru_line.geometry.apply(
    redistribute_vertices, distance=0.1, xarr=lamb.where(np.abs(lamb.lat) > 5)
)

HQ_BORDER = cfeature.NaturalEarthFeature(
    category="cultural",
    name="admin_0_countries",
    scale="10m",
    facecolor="white",
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

depth = 50

criterion = "ZutaGuillen"

_colors = classification_colors[criterion][-4:]

cmap = colors.ListedColormap(_colors[::-1])
bounds = np.arange(len(_colors) + 1)
norm = colors.BoundaryNorm(bounds, cmap.N)

plt.rcParams["font.family"] = "monospace"
fig, ax = plt.subplots(
    figsize=(10, 10), dpi=300, subplot_kw=dict(projection=ccrs.PlateCarree())
)

ax.add_feature(HQ_BORDER, zorder=10)
ax.add_feature(shape200)
ax.add_feature(shape100)
ax.add_feature(shape50)
ross.plot(ax=ax, color="k", ls="--")
format_latlon(ax, ccrs.PlateCarree(), (-110, -60, -30, 10), 2.5, 2.5)

for argo_code in argo_codes:
    _data = (
        float_cont.sel(pcode=argo_code)
        .dropna(dim="TIME", how="all")
        .sel(level=slice(0, depth))
        .mean("level")
    )
    _wm = waterMass(_data.TEMP, _data.PSAL, criterion=criterion)
    for _num, (k, v) in enumerate(_wm.items()):
        _no_null = ~v.isnull()
        _no_last = v.TIME != _data.TIME[-1]
        sca = ax.scatter(
            _data.LONGITUDE[_no_null & _no_last],
            _data.LATITUDE[_no_null & _no_last],
            c=v[_no_null & _no_last],
            cmap=cmap,
            transform=ccrs.PlateCarree(),
            zorder=5 + 2 * _num,
            norm=norm,
            lw=1,
            edgecolor="k",
            s=50,
        )
        if v.TIME[-1] == _data.TIME[-1]:
            ax.scatter(
                _data.LONGITUDE[-1],
                _data.LATITUDE[-1],
                c=v[-1],
                cmap=cmap,
                norm=norm,
                marker="s",
                zorder=200,
                edgecolor="k",
                s=50,
            )
    ax.plot(_data.LONGITUDE, _data.LATITUDE, label=str(argo_code), c="k")

# cbar = plt.colorbar(sca, ticks=bounds[:-1] + 0.5, drawedges=True)
# cbar.set_ticklabels(list(classification[criterion].keys())[:4])
# cbar.ax.invert_yaxis()

ax.set_extent([-85, -70, -20, 0], crs=ccrs.PlateCarree())
ax.grid(ls="--", alpha=0.5)

sca = mlines.Line2D(
    [],
    [],
    markeredgecolor="k",
    color="none",
    marker="s",
    linestyle="none",
    markersize=7,
    label="Latest Position",
)
blue_line = mlines.Line2D(
    [], [], color="k", ls="--", label="Rossby radius\nof deformation", lw=0.8
)
leg2 = plt.legend(
    handles=[blue_line, sca, patch200, patch100, patch50], loc=3, framealpha=0.8
)
leg2.set_zorder(100)
ax.add_artist(leg2)

_leg_list = []
for name, _c in zip(list(classification[criterion].keys())[:4], _colors[::-1]):
    _leg_list.append(
        mlines.Line2D(
            [],
            [],
            markeredgecolor="k",
            color=_c,
            marker="s",
            linestyle="none",
            markersize=7,
            label=locale[name],
        )
    )

leg = plt.legend(handles=_leg_list, loc=1)
leg.set_zorder(100)
ax.add_artist(leg)

# leg = ax.legend(loc=3, title="WMO code")
# leg.set_zorder(100)

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

ax.set_title(
    "Surface (50m depth) Water Mass classification\n"
    "according to Zuta, S., & Guillén, O. (1970)\n"
    "for ARGO floats within 200nm during the last 30 days"
)

fig.savefig(os.path.join(OUT_PATH, "CoastMapWM200nm.png"), bbox_inches="tight")
fig.savefig(
    os.path.join(OUT_PATH, "CoastMapWM200nm.jpeg"), bbox_inches="tight", dpi=200
)
