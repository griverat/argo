import datetime
import os

import argopy
import cmocean as cmo
import geopandas as gpd
import gsw
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import regionmask
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher
from dmelon.ocean.argo import build_dl, launch_shell
from scipy import interpolate

regions = [[-107.5, -101.0, -3, 3], [-87.5, -80, -22, -16]]

### LOAD DATASETS ###

OUTPATH = "/data/users/service/ARGO/FLOATS/output/ARGO-plots"

# Date and region bounds
today = datetime.datetime.today()
idate = today - datetime.timedelta(days=366)
endate = today + datetime.timedelta(days=15)
date_range = [
    f"{idate:%Y-%m-%d}",
    f"{endate:%Y-%m-%d}",
]

godas_clim_leap = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_leap.nc"
).pottmp

godas_clim_normal = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_normal.nc"
).pottmp

# ARGOpy Global options
argopy.set_options(src="localftp", local_ftp="/data/datos/ARGO/gdac")
argopy.set_options(mode="expert")

# Data Fetcher
argo_loader = ArgoDataFetcher(parallel="process", progress=True)

# Index Fetcher
index_loader = ArgoIndexFetcher()

# Load dataframe
for _region in regions:
    argo_df = (
        index_loader.region(_region + date_range).to_dataframe().sort_values("date")
    )
    launch_shell(build_dl(argo_df))

argo_interp = {}
argo_hist = {}

for num, _region in enumerate(regions):
    ds = argo_loader.region(_region + [0, 3000] + date_range).to_xarray()
    ds_profile = ds.argo.point2profile().sortby("TIME")

    # Apply QC to variables of interest
    ds_profile_qc = ds_profile.copy()
    ds_profile_qc["PSAL"] = ds_profile.PSAL.where(ds_profile.PSAL_QC == 1)
    ds_profile_qc["TEMP"] = ds_profile.TEMP.where(ds_profile.TEMP_QC == 1)
    ds_profile_qc["PRES"] = ds_profile.PRES.where(ds_profile.PRES_QC == 1)

    level = np.arange(0, 2100, 1)
    CLIM = {
        "leap": {
            "godas": godas_clim_leap,
        },
        "normal": {
            "godas": godas_clim_normal,
        },
    }

    _cont = []

    for _prof_num in ds_profile_qc.N_PROF.data:
        _sel_prof = ds_profile_qc.sel(N_PROF=_prof_num)
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
            _clim_sel = _clim.sel(
                lat=_sel_prof.LATITUDE,
                lon=np.where(
                    _sel_prof.LONGITUDE < 0,
                    _sel_prof.LONGITUDE + 360,
                    _sel_prof.LONGITUDE,
                ),
                time=f"{_clim.time.dt.year[0].data}-{pd.to_datetime(_sel_prof.TIME.data):%m-%d}",
                method="nearest",
            ).load()
            if _clim_sel.level[0].data != 0:
                _clim_sel = xr.DataArray(
                    np.concatenate((_clim_sel[[0]], _clim_sel)),
                    coords=[("level", np.concatenate(([0], _clim_sel.level)))],
                )

            TEMP_anom = _interp.TEMP - _clim_sel.interp_like(_interp.TEMP)

            _interp[f"TEMP_anom_{source}"] = TEMP_anom

        _cont.append(_interp)
    argo_interp[str(num)] = (
        xr.concat(_cont, dim="TIME").interpolate_na(dim="level").load()
    )
    argo_hist[str(num)] = (
        argo_interp[str(num)].TEMP_anom_godas.isel(level=0).resample(TIME="D").count()
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


def format_degree(num, kind="latitude"):
    pos = "°N"
    neg = "°S"
    if kind == "longitude":
        pos = "°E"
        neg = "°W"
    return f"{abs(num):2.1f}{pos if num > 0 else neg if num < 0 else ''}"


import matplotlib.dates as mdates

month_locator = mdates.MonthLocator()
month_formatter = mdates.DateFormatter("%^b")

year_locator = mdates.YearLocator()
year_formatter = mdates.DateFormatter("%Y")

clevs = [-6, -5, -4, -3, -2, -1, -0.5, 0.5, 1, 2, 3, 4, 5, 6]
norm = mpl.colors.BoundaryNorm(clevs, cmap.N)

plt.rcParams["font.family"] = "monospace"
fig = plt.figure(dpi=300, constrained_layout=False, figsize=(10, 7))
gs = fig.add_gridspec(nrows=2, ncols=1, hspace=0.2)
gs1 = gs[0].subgridspec(nrows=2, ncols=1, hspace=0, height_ratios=[4, 1])
gs2 = gs[1].subgridspec(nrows=2, ncols=1, hspace=0, height_ratios=[4, 1])

min_time = [_da.TIME.min() for _da in argo_interp.values()]
min_time = max(min_time)
max_time = [_da.TIME.max() for _da in argo_interp.values()]
max_time = max(max_time)

for _gs, argo_region_interp, _argo_hist in zip(
    [gs1, gs2], argo_interp.values(), argo_hist.values()
):
    _plot_data = (
        argo_region_interp.interpolate_na(dim="TIME")
        .interpolate_na(dim="level")
        .rolling(TIME=5, center=True, min_periods=1)
        .mean()
    )

    ax0 = fig.add_subplot(_gs[0])

    hov = _plot_data.TEMP_anom_godas.plot.contourf(
        ax=ax0,
        x="TIME",
        yincrease=False,
        cmap=cmap,
        norm=norm,
        extend="both",
        add_colorbar=False,
    )

    cont = _plot_data.TEMP_anom_godas.plot.contour(
        ax=ax0, x="TIME", yincrease=False, colors="k", norm=norm, linewidths=0.5
    )

    clabs = ax0.clabel(cont, fontsize=7, inline=False)

    for l in clabs:
        l.set_rotation(0)
        l.set_bbox(dict(facecolor="white", edgecolor="none", pad=0))

    ax0.set_ylim(500, 0)
    ax0.set_xlabel("")
    ax0.set_ylabel("Depth")
    ax0.set_yticks(np.arange(0, 501, 50))
    ax0.tick_params(labelbottom=False)
    ax0.xaxis.set_minor_locator(month_locator)
    ax0.xaxis.set_minor_formatter(month_formatter)
    ax0.xaxis.set_major_locator(year_locator)
    ax0.xaxis.set_major_formatter(year_formatter)
    # ax0.set_xlim(argo_hist.TIME.min(), argo_hist.TIME.max())
    ax0.grid(ls="dotted", which="both", lw=1, alpha=0.5)
    ax0.set_xlim(min_time, max_time)
    ax0.text(
        x=0,
        y=1.05,
        s=f"Latest data: {pd.to_datetime(_plot_data.TIME.max().data):%d%^b%Y}",
        horizontalalignment="left",
        verticalalignment="center",
        transform=ax0.transAxes,
        fontsize=9,
    )

    ax1 = fig.add_subplot(_gs[1], sharex=ax0)
    ax1.bar(_argo_hist.TIME, _argo_hist, color="k")
    ax1.set_ylim(0, 6)
    # ax1.set_xlim(_argo_hist.TIME.min(), _argo_hist.TIME.max())
    ax1.tick_params(
        axis="y", which="both", left=False, right=True, labelleft=False, labelright=True
    )
    ax1.set_ylabel("Count", rotation=-90, labelpad=10)
    ax1.yaxis.set_label_position("right")
    ax1.set_yticks(np.arange(0, 6.1, 2))
    ax1.set_yticks(np.arange(1, 6, 2), minor=True)

    ax1.grid(ls="dotted", which="both", lw=1, alpha=0.5)

    ax1.xaxis.set_minor_locator(month_locator)
    ax1.xaxis.set_minor_formatter(month_formatter)
    ax1.xaxis.set_major_locator(year_locator)
    ax1.xaxis.set_major_formatter(year_formatter)
    ax1.xaxis.remove_overlapping_locs = False
    ax1.tick_params(axis="x", which="major", pad=12)
    ax1.tick_params(axis="x", labelrotation=0)
    for xlabels in ax1.get_xticklabels():
        xlabels.set_ha("center")
ax0.text(
    x=0.5,
    y=2.75,
    s="Sea temperature profile anomalies with daily histogram of ARGO data count over:\n"
    f"(a) [{format_degree(regions[0][0], 'longitude')}-{format_degree(regions[0][1], 'longitude')}] [{format_degree(regions[0][2])}-{format_degree(regions[0][3])}] and "
    f"(b) [{format_degree(regions[1][0], 'longitude')}-{format_degree(regions[1][1], 'longitude')}] [{format_degree(regions[1][2])}-{format_degree(regions[1][3])}]",
    horizontalalignment="center",
    verticalalignment="top",
    transform=ax0.transAxes,
)
ax0.text(
    x=0.67,
    y=-0.45,
    s="Source: ARGO GDAC      Processing: IGP\n" "Clim: GODAS 1981-2010",
    horizontalalignment="left",
    verticalalignment="top",
    transform=ax0.transAxes,
    fontsize=8,
)
fig.savefig(os.path.join(OUTPATH, f"argoRegions.png"), dpi=300, bbox_inches="tight")
# fig.savefig(os.path.join(OUTPATH, f"argoRegions.pdf"), dpi=300, bbox_inches="tight")
