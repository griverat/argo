import os

import argopy
import numpy as np
import pandas as pd
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher
from scipy import interpolate

# ARGOpy options
argopy.set_options(src="localftp", local_ftp="/data/datos/ARGO/gdac")
argopy.set_options(mode="expert")

# ARGOpy loaders
argo_loader = ArgoDataFetcher(parallel="process", progress=True)
index_loader = ArgoIndexFetcher()

OUTPATH = "/data/users/service/ARGO/FLOATS/output/ARGO-singleprof"

# ARGO data

argo_codes = [
    6903002,
    6903003,
    3901809,
    6902963,
    3901808,
    6903000,
    6903001,
    6902961,
    6903004,
    6902962,
    6903005,
]

argo_df = index_loader.float(argo_codes).to_dataframe()

ds = argo_loader.float(argo_codes).to_xarray()

ds_profile = ds.argo.point2profile()


# godas_clim = xr.open_dataset(
#     "/data/users/grivera/GODAS/clim/monthly/godas_monthclim.nc"
# ).pottmp
# # Copy first value to 0-level
# godas_zero = godas_clim.isel(level=0)
# godas_zero["level"] = 0
# godas_clim = xr.concat([godas_zero, godas_clim], dim="level")


# Climatology loading
print("Opening GODAS monthly climatology")

godas_clim_leap = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_leap.nc"
).pottmp
godas_clim_normal = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/godas_clim_normal.nc"
).pottmp

print("Opening SODA monthly climatology")

soda_clim_leap = xr.open_dataset("/data/users/grivera/SODA/clim/soda_clim_leap.nc").temp
soda_clim_normal = xr.open_dataset(
    "/data/users/grivera/SODA/clim/soda_clim_normal.nc"
).temp

print("Opening IMARPE monthly climatology")

imarpe_clim_leap = xr.open_dataset(
    "/data/users/grivera/IMARPE/clim/imarpe_clim_leap.nc"
).temperature
imarpe_clim_normal = xr.open_dataset(
    "/data/users/grivera/IMARPE/clim/imarpe_clim_normal.nc"
).temperature

CLIM = {
    "leap": {
        "climGODAS": godas_clim_leap,
        "climIMARPE": imarpe_clim_leap,
        "climSODA": soda_clim_leap,
    },
    "normal": {
        "climGODAS": godas_clim_normal,
        "climIMARPE": imarpe_clim_normal,
        "climSODA": soda_clim_normal,
    },
}

argo_codes = (
    argo_df.sort_values("date")
    .groupby("wmo")
    .nth(-1)
    .sort_values("latitude", ascending=False)
    .index.tolist()
)

## PLOTTING

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import gsw
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from cartopy.io.shapereader import Reader
from dmelon.plotting import HQ_BORDER, format_latlon
from matplotlib.patches import Patch

# _clim = "climIMARPE"
var = "anomTemp"
ylim = (0, 500)
lon_corr = 0

HQ_SA = cfeature.NaturalEarthFeature(
    category="cultural",
    name="admin_0_countries",
    scale="10m",
    facecolor="white",  # cfeature.COLORS['land'],
    edgecolor="black",
    linewidth=1.5,
)

level = np.arange(0, 900, 10)

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

for _num, argo_code in enumerate(argo_codes):
    argo_sel = ds_profile.where(ds_profile.PLATFORM_NUMBER == argo_code).dropna(
        dim="N_PROF", how="all"
    )
    print(argo_code)

    level = np.arange(0, 2100, 1)

    _cont = []

    for _prof_num in argo_sel.N_PROF.data:
        _sel_prof = argo_sel.sel(N_PROF=_prof_num)
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

            _interp[source] = TEMP_anom

        _cont.append(_interp)
    argo_sel_interp = xr.concat(_cont, dim="TIME").interpolate_na(dim="level").load()
    argo_sel_interp["PLATFORM_NUMBER"] = [argo_code]

    prof_pos = argo_df.query("wmo==@argo_code").sort_values("date")
    prof_pos["label"] = (
        prof_pos.file.str.split("_").str[-1].str.split(".").str[0].str.lstrip("0")
    )

    for _clim in _CLIM.keys():
        ## PLOT ##
        fig = plt.figure(constrained_layout=True, figsize=(10, 3), dpi=300)
        spec = gridspec.GridSpec(ncols=6, nrows=2, figure=fig)
        f_ax1 = fig.add_subplot(spec[:, :2], projection=ccrs.PlateCarree())
        f_ax2 = fig.add_subplot(spec[:, 2])
        f_ax3 = fig.add_subplot(spec[:, 3], sharey=f_ax2, sharex=f_ax2)
        f_ax4 = fig.add_subplot(spec[:, 4], sharey=f_ax2, sharex=f_ax2)
        f_ax5 = fig.add_subplot(spec[:, 5], sharey=f_ax2, sharex=f_ax2)

        ### MAP ###

        llat, llon = prof_pos.latitude.iloc[-1], prof_pos.longitude.iloc[-1]

        delta = 1.2
        extent = (llon - delta, llon + delta, llat - delta, llat + delta)
        extent_l = tuple(map(round, map(sum, zip(extent, (-5, 5, -5, 5)))))

        format_latlon(
            f_ax1,
            proj=ccrs.PlateCarree(),
            latlon_bnds=extent_l,
            lon_step=0.5,
            lat_step=0.5,
            nformat=".1f",
        )
        f_ax1.plot(
            prof_pos.longitude.iloc[-10:],
            prof_pos.latitude.iloc[-10:],
            transform=ccrs.PlateCarree(),
            lw=0.5,
            c="k",
        )
        f_ax1.scatter(
            prof_pos.longitude.iloc[-10:-1],
            prof_pos.latitude.iloc[-10:-1],
            transform=ccrs.PlateCarree(),
            s=3,
            zorder=10,
        )

        f_ax1.scatter(
            prof_pos.longitude.iloc[-1:],
            prof_pos.latitude.iloc[-1:],
            transform=ccrs.PlateCarree(),
            s=10,
            c="r",
            zorder=10,
        )
        f_ax1.tick_params(axis="both", which="major", labelsize=7)
        f_ax1.set_extent(extent, crs=ccrs.PlateCarree())
        for row in prof_pos[["label", "longitude", "latitude"]].iloc[-10:].itertuples():
            f_ax1.annotate(
                row.label, (row.longitude, row.latitude), va="baseline", zorder=11
            )

        # SHAPES
        f_ax1.add_feature(shape200)
        f_ax1.add_feature(shape100)
        f_ax1.add_feature(shape50, label="50 nm")
        f_ax1.add_feature(HQ_SA)

        f_ax1.legend(
            handles=[patch200, patch100, patch50], loc="lower left", fontsize=8
        ).set_zorder(20)

        f_ax1.grid(ls="--", lw="0.5", alpha=0.5)
        f_ax1.set_title(f"Profile #{argo_sel_interp.PLATFORM_NUMBER[0].data:.0f}")

        ### PROFILES ###
        for num, ax in zip(np.arange(-4, 0, 1), [f_ax2, f_ax3, f_ax4, f_ax5]):

            anom = argo_sel_interp[_clim].isel(TIME=num, drop=True)
            anom = anom.rolling(level=21, min_periods=1, center=True).mean()

            anom.plot(y="level", yincrease=False, ax=ax, c="k", lw=0.5)

            ax.fill_betweenx(
                anom.level, anom, 0, where=anom > 0, color="r", interpolate=True
            )
            ax.fill_betweenx(
                anom.level, anom, 0, where=anom < 0, color="b", interpolate=True
            )
            ax.axvline(ls="--", c="k", lw=0.5)

            ax.set_title(f"{pd.to_datetime(argo_sel_interp.TIME[num].data):%d-%b-%Y}")
            ax.set_ylabel("")
            ax.set_xlabel("")
            ax.tick_params(axis="both", which="major", labelsize=7)
            if num == -4:
                ax.set_ylabel("Depth [m]")
                ax.set_ylim(ylim[1], ylim[0])
                ax.set_xticks(np.arange(-30, 30, 1.5))
                ax.set_xlim(-3.5, 3.5)
            else:
                ax.tick_params(axis="y", labelleft=False)

            ax.grid(ls="--", lw="0.5", alpha=0.5)
            ax.annotate(
                prof_pos.label.iloc[num],
                xy=(0.1, 0.1),
                xycoords="axes fraction",
                bbox=dict(boxstyle="round", fc=None, fill=False),
            )
        fig.text(
            0.66,
            -0.02,
            "Vertical Sea Temperature Anomaly [°C]",
            ha="center",
            va="center",
        )
        fig.text(
            0.02,
            -0.05,
            f"Clim: {_clim[4:].upper()} 1981-2010\nProcessing: IGP",
            fontsize=6,
        )
        fig.text(
            0.3,
            -0.01,
            f"*Only the last 10 data points are shown",
            ha="right",
            va="center",
            fontsize=5,
        )

        fig.savefig(
            os.path.join(
                OUTPATH,
                f"{argo_sel_interp.PLATFORM_NUMBER[0].data:.0f}_{var}_{ylim[0]}_{ylim[1]}m_{_clim}.png",
            ),
            bbox_inches="tight",
        )

        fig.savefig(
            os.path.join(
                OUTPATH, f"singleProf{_num+1}_{var}_{ylim[0]}_{ylim[1]}m_{_clim}.png"
            ),
            bbox_inches="tight",
        )
        plt.close(fig)
