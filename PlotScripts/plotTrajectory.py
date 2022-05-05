import datetime
import os

import argopy
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher
from dmelon.ocean.argo import build_dl, launch_shell
from dmelon.utils import check_folder, findPointsInPolys
from scipy import interpolate

# ARGOpy global options
argopy.set_options(src="localftp", local_ftp="/data/datos/ARGO/gdac")
argopy.set_options(mode="expert")


# ARGO data fetcher
argo_loader = ArgoDataFetcher(parallel="process", progress=True)
index_loader = ArgoIndexFetcher()


# Data loading parameters
argo_region = [-90, -70, -20, -2.5]
today = datetime.datetime.today()
idate = today - datetime.timedelta(days=20)
endate = today + datetime.timedelta(days=15)
date_range = [
    f"{idate:%Y-%m-%d}",
    f"{endate:%Y-%m-%d}",
]

argo_df = (
    index_loader.region(argo_region + date_range).to_dataframe().sort_values("date")
)


# Read and mask with 200nm shapefile
mask200 = gpd.read_file("/data/users/grivera/Shapes/NEW_MASK/200mn_full.shp")
pointInPolys = findPointsInPolys(argo_df, mask200)


# on-demand update of floats to be used
launch_shell(build_dl(pointInPolys))


# ARGO DATA LOADING
argo_codes = (
    pointInPolys.sort_values("date")
    .groupby("wmo")
    .nth(-1)
    .sort_values("latitude", ascending=False)
    .index.tolist()
)
ds = argo_loader.float(argo_codes).to_xarray()

ds_profile = ds.argo.point2profile().sortby("TIME")


# Apply QC to variables of interest
ds_profile_qc = ds_profile.copy()
ds_profile_qc["PSAL"] = ds_profile.PSAL.where(ds_profile.PSAL_QC == 1)
ds_profile_qc["TEMP"] = ds_profile.TEMP.where(ds_profile.TEMP_QC == 1)
ds_profile_qc["PRES"] = ds_profile.PRES.where(ds_profile.PRES_QC == 1)


# Climatology loading
godas_clim_leap = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_leap.nc"
).pottmp
godas_clim_normal = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_normal.nc"
).pottmp

soda_clim_leap = xr.open_dataset("/data/users/grivera/SODA/clim/soda_clim_leap.nc").temp
soda_clim_normal = xr.open_dataset(
    "/data/users/grivera/SODA/clim/soda_clim_normal.nc"
).temp

imarpe_clim_leap = xr.open_dataset(
    "/data/users/grivera/IMARPE/clim/imarpe_clim_leap.nc"
).temperature
imarpe_clim_normal = xr.open_dataset(
    "/data/users/grivera/IMARPE/clim/imarpe_clim_normal.nc"
).temperature

CLIM = {
    "leap": {
        "godas": godas_clim_leap,
        "imarpe": imarpe_clim_leap,
        "soda": soda_clim_leap,
    },
    "normal": {
        "godas": godas_clim_normal,
        "imarpe": imarpe_clim_normal,
        "soda": soda_clim_normal,
    },
}


# Plot parameters

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import gsw
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from cartopy.io.shapereader import Reader
from dmelon.plotting import format_latlon
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
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
        parts = [redistribute_vertices(part, distance, xarr) for part in geom]
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


HQ_SA = cfeature.NaturalEarthFeature(
    category="cultural",
    name="admin_0_countries",
    scale="10m",
    facecolor="white",  # cfeature.COLORS['land'],
    edgecolor="black",
    linewidth=1.5,
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
ross_line = Line2D(
    [], [], color="k", ls="--", label="Rossby radius\nof deformation", lw=0.8
)
lpos = Line2D(
    [0],
    [0],
    marker=r"$\bigodot$",
    color="none",
    label="Latest position",
    markerfacecolor="none",
    markeredgecolor="k",
    markersize=10,
)

rgbset2 = {
    0: "#FFFFFF",
    21: "#FFFAAA",
    22: "#FFE878",
    23: "#FFC03C",
    24: "#FFA000",
    25: "#FF6000",
    26: "#FF3200",
    27: "#E11400",
    28: "#C00000",
    29: "#A50000",
    41: "#E1FFFF",
    42: "#B4F0FA",
    43: "#96D2FA",
    44: "#78B9FA",
    45: "#50A5F5",
    46: "#3C96F5",
    47: "#2882F0",
    48: "#1E6EEB",
    49: "#1464D2",
}

ccols = [49, 48, 47, 46, 44, 42, 41, 0, 21, 22, 24, 26, 27, 28, 29]
cmap = mpl.colors.ListedColormap([rgbset2[cnum] for cnum in ccols[1:-1]]).with_extremes(
    over=rgbset2[ccols[-1]], under=rgbset2[ccols[0]]
)
clevs = [-6, -5, -4, -3, -2, -1, -0.5, 0.5, 1, 2, 3, 4, 5, 6]
norm = mpl.colors.BoundaryNorm(clevs, cmap.N)

month_locator = mdates.MonthLocator()
month_formatter = mdates.DateFormatter("%^b")

year_locator = mdates.YearLocator()
year_formatter = mdates.DateFormatter("%Y")

depth = 500

SORTED_DIR = os.path.join("/data/users/service/ARGO/FLOATS/output/floats", "sorted")
check_folder(SORTED_DIR)

for order, argo_code in enumerate(argo_codes):
    print(f"Processing ARGO float #{argo_code}")
    OUT_DIR = os.path.join(
        "/data/users/service/ARGO/FLOATS/output/floats", str(argo_code)
    )
    check_folder(OUT_DIR)

    _argo_profile = (
        ds_profile_qc.copy()
        .where(ds_profile.PLATFORM_NUMBER == argo_code)
        .dropna(dim="N_PROF", how="all")
    )

    level = np.arange(0, 2100, 1)

    _cont = []

    for _prof_num in _argo_profile.N_PROF.data:
        _sel_prof = _argo_profile.sel(N_PROF=_prof_num)
        _non_nan_index = _sel_prof.PRES.dropna("N_LEVELS").N_LEVELS
        _PRES = _sel_prof.PRES.sel(N_LEVELS=_non_nan_index).data
        _TEMP = _sel_prof.TEMP.sel(N_LEVELS=_non_nan_index).data
        _PSAL = _sel_prof.PSAL.sel(N_LEVELS=_non_nan_index).data

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
            coords=dict(
                level=(["level"], level),
                TIME=_sel_prof.TIME,
            ),
        )

        if _sel_prof.TIME.dt.is_leap_year.data:
            _CLIM = CLIM["leap"]
        else:
            _CLIM = CLIM["normal"]

        for source, _clim in _CLIM.items():
            _clim_sel = (
                _clim.sel(
                    time=f"{_clim.time.dt.year[0].data}-{pd.to_datetime(_sel_prof.TIME.data):%m-%d}",
                )
                .ffill(dim="lat")
                .sel(
                    lat=_sel_prof.LATITUDE,
                    lon=np.where(
                        _sel_prof.LONGITUDE < 0,
                        _sel_prof.LONGITUDE + 360,
                        _sel_prof.LONGITUDE,
                    ),
                    method="nearest",
                )
                .load()
            )
            if _clim_sel.level[0].data != 0:
                _clim_sel = xr.DataArray(
                    np.concatenate((_clim_sel[[0]], _clim_sel)),
                    coords=[("level", np.concatenate(([0], _clim_sel.level)))],
                )

            TEMP_anom = _interp.TEMP - _clim_sel.interp_like(_interp.TEMP)

            _interp[f"TEMP_anom_{source}"] = TEMP_anom

        _cont.append(_interp)

    argo_float_interp = xr.concat(_cont, dim="TIME").interpolate_na(dim="level").load()

    sdate = pd.to_datetime(argo_float_interp.TIME.max().data) - pd.Timedelta("365D")
    _data = (
        argo_float_interp.where(argo_float_interp.TIME > sdate)
        .dropna(dim="TIME", how="all")
        .rolling(TIME=3, center=True, min_periods=1)
        .mean()
    )

    lat_center = (_data.LATITUDE.min().data + _data.LATITUDE.max().data) / 2
    lon_center = (_data.LONGITUDE.min().data + _data.LONGITUDE.max().data) / 2

    lat_delta = (_data.LATITUDE.max().data - _data.LATITUDE.min().data) / 2
    lon_delta = (_data.LONGITUDE.max().data - _data.LONGITUDE.min().data) / 2

    if lat_delta > lon_delta:
        lat_delta += 1
        lon_delta = lat_delta / 1.35
    else:
        lon_delta += 1
        lat_delta = lon_delta * 1.35

    bnds = [
        lon_center - lon_delta,
        lon_center + lon_delta,
        lat_center - lat_delta,
        lat_center + lat_delta,
    ]

    plt.rcParams["font.family"] = "monospace"
    fig = plt.figure(constrained_layout=False, figsize=(11, 8.5), dpi=300)
    gs = fig.add_gridspec(
        nrows=3, ncols=2, wspace=0.12, hspace=0.21, width_ratios=[1, 1]
    )

    ## TOP FIGURE ##############################################################
    ax0 = fig.add_subplot(gs[0, 0])
    cont = _data.TEMP_anom_godas.plot.contourf(
        ax=ax0,
        y="level",
        yincrease=False,
        cmap=cmap,
        norm=norm,
        extend="both",
        add_colorbar=False,
    )

    _cont0 = _data.TEMP_anom_godas.plot.contour(
        ax=ax0,
        y="level",
        yincrease=False,
        norm=norm,
        add_colorbar=False,
        colors="k",
        linewidths=0.5,
    )

    ax0.set_ylim(depth, 0)
    ax0.set_title("Sea Temperature profile anomalies (°C)")
    ax0.set_ylabel("Depth (m)")
    ax0.set_xlabel("")

    ## MID FIGURE ##############################################################
    ax1 = fig.add_subplot(gs[1, 0], sharey=ax0, sharex=ax0)
    _data.TEMP_anom_soda.plot.contourf(
        ax=ax1,
        y="level",
        yincrease=False,
        cmap=cmap,
        norm=norm,
        extend="both",
        add_colorbar=False,
    )

    _cont1 = _data.TEMP_anom_soda.plot.contour(
        ax=ax1,
        y="level",
        yincrease=False,
        norm=norm,
        add_colorbar=False,
        colors="k",
        linewidths=0.5,
    )
    ax1.set_title("")
    ax1.set_ylabel("Depth (m)")
    ax1.set_xlabel("")

    ## BOTTOM FIGURE ##############################################################
    ax2 = fig.add_subplot(gs[2, 0], sharey=ax0, sharex=ax0)
    _data.TEMP_anom_imarpe.plot.contourf(
        ax=ax2,
        y="level",
        yincrease=False,
        cmap=cmap,
        norm=norm,
        extend="both",
        add_colorbar=False,
    )

    _cont2 = _data.TEMP_anom_imarpe.plot.contour(
        ax=ax2,
        y="level",
        yincrease=False,
        norm=norm,
        add_colorbar=False,
        colors="k",
        linewidths=0.5,
    )
    ax2.tick_params(axis="x", labelrotation=0)  # , which="major", pad=10)
    ax2.set_title("")
    ax2.set_ylabel("Depth (m)")
    ax2.set_xlabel("")

    ## MAP ##############################################################
    ax3 = fig.add_subplot(gs[:, 1], projection=ccrs.PlateCarree())

    points = np.array([_data.LONGITUDE.data, _data.LATITUDE.data]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    vals = np.linspace(0, 100, _data.LONGITUDE.size)

    _norm = plt.Normalize(vals.min(), vals.max())
    lc = LineCollection(segments, cmap="rainbow", norm=_norm)
    # Set the values used for colormapping
    lc.set_array(vals)
    lc.set_linewidth(3)
    line = ax3.add_collection(lc)

    ax3.scatter(
        _data.LONGITUDE,
        _data.LATITUDE,
        transform=ccrs.PlateCarree(),
        marker=".",
        c="k",
        s=5,
        zorder=100,
    )

    ax3.scatter(
        _data.LONGITUDE[-1],
        _data.LATITUDE[-1],
        transform=ccrs.PlateCarree(),
        marker=r"$\bigodot$",
        edgecolors="k",
        s=50,
        zorder=100,
        facecolors="none",
    )

    format_latlon(ax3, proj=ccrs.PlateCarree(), lon_step=1, lat_step=1)

    ax3.add_feature(shape200)
    ax3.add_feature(shape100)
    ax3.add_feature(shape50)
    ax3.add_feature(HQ_SA)

    lpos = Line2D(
        [0],
        [0],
        marker=r"$\bigodot$",
        color="none",
        label="Latest position",
        markerfacecolor="none",
        markeredgecolor="k",
        markersize=10,
    )

    ax3.legend(
        handles=[lpos, patch200, patch100, patch50], loc="lower left", fontsize=10
    ).set_zorder(20)

    ax3.set_extent(bnds, crs=ccrs.PlateCarree())

    ## TEXT ##############################################################
    ax3.text(
        x=0.5,
        y=1.08,
        s=f"Trajectory of\nARGO float #{argo_code}",
        horizontalalignment="center",
        verticalalignment="center",
        transform=ax3.transAxes,
        fontsize=15,
    )

    ax3.text(
        x=0.5,
        y=1.025,
        s=f"{pd.to_datetime(_data.TIME.min().data):%d%^b%Y} - {pd.to_datetime(_data.TIME.max().data):%d%^b%Y}",
        horizontalalignment="center",
        verticalalignment="center",
        transform=ax3.transAxes,
    )

    ax3.text(
        x=-0.02,
        y=-0.07,
        s=f"Source: ARGO GDAC    Processing: IGP    Latest data: {pd.to_datetime(_data.TIME.max().data):%d%^b%Y}",
        horizontalalignment="left",
        verticalalignment="center",
        transform=ax3.transAxes,
        fontsize=8,
    )

    ax3.text(
        x=-0.02,
        y=-0.11,
        s=f"Clim: 1981-2010   -   a) GODAS,  b) SODA,  c) IMARPE\n3-point running mean",
        horizontalalignment="left",
        verticalalignment="center",
        transform=ax3.transAxes,
        fontsize=8,
    )

    ## COLORBAR ##############################################################

    axins = inset_axes(
        ax2,
        width="110%",
        height="5%",
        loc="lower center",
        bbox_to_anchor=(0.0, -0.25, 1, 1),
        bbox_transform=ax2.transAxes,
        borderpad=0,
    )
    cbar = fig.colorbar(
        cont, cax=axins, ticks=clevs, orientation="horizontal", drawedges=True
    )
    cbar.ax.set_xticklabels([str(l) for l in clevs])
    cbar.ax.tick_params(labelsize=8, pad=-2, bottom=False)

    def fmt(x):
        s = f"{x:.1f}"
        if s.endswith("0"):
            s = f"{x:.0f}"
        return f"{s}"

    conts = [_cont0, _cont1, _cont2]
    letters = ["a)", "b)", "c)", "d)"]

    ## COMMON ##############################################################
    for num, _ax in enumerate([ax0, ax1, ax2, ax3]):
        _ax.grid(which="both", ls="dotted", lw=1.5, alpha=0.5)
        _ax.text(
            x=0.02,
            y=0.97,
            s=f"{letters[num]}",
            horizontalalignment="left",
            verticalalignment="top",
            transform=_ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.5),
            zorder=150,
            weight="bold",
        )

        if num != 3:
            _ax.xaxis.set_minor_locator(month_locator)
            _ax.xaxis.set_minor_formatter(month_formatter)
            _ax.xaxis.set_major_locator(year_locator)
            _ax.xaxis.set_major_formatter(year_formatter)
            _ax.xaxis.remove_overlapping_locs = False
            _ax.tick_params(axis="x", which="major", pad=12)
            _ax.tick_params(axis="x", labelrotation=0)
            for xlabels in _ax.get_xticklabels():
                xlabels.set_ha("center")

            _clabel = _ax.clabel(conts[num], fontsize=7, inline=False, fmt=fmt)

            for l in _clabel:
                l.set_rotation(0)
                l.set_bbox(dict(facecolor="white", edgecolor="none", pad=0, alpha=0.7))

            points = np.array(
                [
                    mdates.date2num(_data.TIME.data),
                    np.full_like(_data.TIME, depth, dtype=int),
                ]
            ).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            vals = np.linspace(0, 100, _data.TIME.size)

            _norm = plt.Normalize(vals.min(), vals.max())
            lc = LineCollection(segments, cmap="rainbow", norm=_norm)
            # Set the values used for colormapping
            lc.set_array(vals)
            lc.set_linewidth(3)
            line = _ax.add_collection(lc)
            line.set_zorder(50)
            line.set_clip_on(False)

            _ax.scatter(
                _data.TIME,
                np.full_like(_data.TIME, depth, dtype=int),
                c="k",
                s=2,
                marker=".",
                clip_on=False,
                zorder=60,
            )

    # Save figure
    savefig_kwargs = dict(dpi=300, bbox_inches="tight")
    fig.savefig(
        os.path.join(SORTED_DIR, f"prof{order:02.0f}_traj.png"), **savefig_kwargs
    )
    fig.savefig(
        os.path.join(OUT_DIR, f"prof{argo_code}_traj_latest.png"), **savefig_kwargs
    )
    fig.savefig(
        os.path.join(OUT_DIR, f"prof{argo_code}_traj_latest.pdf"), **savefig_kwargs
    )
    fig.savefig(
        os.path.join(
            OUT_DIR,
            f"prof{argo_code}_traj_{pd.to_datetime(_data.TIME.max().data):%d%^b%Y}.png",
        ),
        **savefig_kwargs,
    )
    fig.savefig(
        os.path.join(
            OUT_DIR,
            f"prof{argo_code}_traj_{pd.to_datetime(_data.TIME.max().data):%d%^b%Y}.pdf",
        ),
        **savefig_kwargs,
    )
