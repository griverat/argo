import os
import argopy
import numpy as np
import pandas as pd
import xarray as xr
from argopy import DataFetcher as ArgoDataFetcher
from argopy import IndexFetcher as ArgoIndexFetcher

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


print("Opening GODAS monthly climatology")

godas_clim = xr.open_dataset(
    "/data/users/grivera/GODAS/clim/monthly/godas_monthclim.nc"
).pottmp
# Copy first value to 0-level
godas_zero = godas_clim.isel(level=0)
godas_zero["level"] = 0
godas_clim = xr.concat([godas_zero, godas_clim], dim="level")


print("Opening IMARPE monthly climatology")

imarpe_clim = xr.open_dataset(
    "/data/users/grivera/IMARPE/MonthlyTSOClimatology.nc"
).temperature.rename(depth="level", latitude="lat", longitude="lon")

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
from dmelon.plotting import format_latlon

clim = imarpe_clim
_clim = "IMARPE"
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

for _num, argo_code in enumerate(argo_codes):
    argo_sel = ds_profile.where(ds_profile.PLATFORM_NUMBER == argo_code).dropna(
        dim="N_PROF", how="all"
    )
    print(argo_code)
    argo_sel_interp = argo_sel.argo.interp_std_levels(level)
    argo_sel_interp = argo_sel_interp.swap_dims(N_PROF="TIME").sortby("TIME")

    prof_pos = argo_df.query("wmo==@argo_code").sort_values("date")
    prof_pos["label"] = (
        prof_pos.file.str.split("_").str[-1].str.split(".").str[0].str.lstrip("0")
    )

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

    delta = 1
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
    )

    f_ax1.scatter(
        prof_pos.longitude.iloc[-1:],
        prof_pos.latitude.iloc[-1:],
        transform=ccrs.PlateCarree(),
        s=10,
        c="r",
    )

    f_ax1.set_extent(extent, crs=ccrs.PlateCarree())
    for row in prof_pos[["label", "longitude", "latitude"]].iloc[-10:].itertuples():
        f_ax1.annotate(row.label, (row.longitude, row.latitude), va="baseline")
    f_ax1.add_feature(HQ_SA)
    f_ax1.grid(ls="--", lw="0.5", alpha=0.5)
    f_ax1.set_title(f"Profile #{argo_sel_interp.PLATFORM_NUMBER[0].data:.0f}")
    plt.figtext(
        0.02, 0, f"Clim: {_clim.upper()} 1981-2010\nProcessing: IGP", fontsize=5
    )

    ### PROFILES ###

    for num, ax in zip(np.arange(-4, 0, 1), [f_ax2, f_ax3, f_ax4, f_ax5]):

        argo_sel_plot = argo_sel_interp.TEMP.isel(TIME=num, drop=True)
        argo_sel_plot["level"] = (
            gsw.z_from_p(argo_sel_plot.PRES_INTERPOLATED, argo_sel_plot.LATITUDE) * -1
        )

        # argo_sel_plot.plot(y="level", yincrease=False, ax=ax, c="r")
        argo_sel_plot_interp = argo_sel_plot.swap_dims(
            PRES_INTERPOLATED="level"
        ).interp(level=level, kwargs=dict(fill_value="extrapolate"))

        clim_plot = clim.sel(
            lat=argo_sel_plot.LATITUDE,
            lon=argo_sel_plot.LONGITUDE + lon_corr,
            method="nearest",
            drop=True,
        ).sel(month=argo_sel_interp.TIME[num].dt.month.data, drop=True)

        clim_plot_interp = clim_plot.interp(
            level=level, kwargs=dict(fill_value="extrapolate")
        )

        anom = argo_sel_plot_interp - clim_plot_interp
        anom = anom.rolling(level=3, min_periods=1, center=True).mean()

        anom.plot(y="level", yincrease=False, ax=ax, c="k", lw=0.5)

        ax.fill_betweenx(
            anom.level, anom, 0, where=anom > 0, color="r", interpolate=True
        )
        ax.fill_betweenx(
            anom.level, anom, 0, where=anom < 0, color="b", interpolate=True
        )
        ax.axvline(ls="--", c="k", lw=0.5)

        # godas_clim_plot.plot(ax=ax, y="level", yincrease=False, ls="--", lw=0.7, c="k")

        ax.set_title(f"{pd.to_datetime(argo_sel_interp.TIME[num].data):%d-%b-%Y}")
        ax.set_ylabel("")
        ax.set_xlabel("Temperature [°C]")
        ax.tick_params(axis="both", which="major", labelsize=8)
        if num == -4:
            ax.set_ylabel("Depth [m]")
            ax.set_ylim(500, 0)
            ax.set_xticks(np.arange(-30, 30, 1.5))
            # ax.set_xlim(0, 25)
            ax.set_xlim(-3, 3)
        else:
            ax.tick_params(axis="y", labelleft=False)

        ax.grid(ls="--", lw="0.5", alpha=0.5)
        ax.annotate(
            prof_pos.label.iloc[num],
            xy=(0.1, 0.1),
            xycoords="axes fraction",
            bbox=dict(boxstyle="round", fc=None, fill=False),
        )
    fig.savefig(
        os.path.join(
            OUTPATH, f"prof{argo_sel_interp.PLATFORM_NUMBER[0].data:.0f}_{_clim}.png"
        ),
        bbox_inches="tight",
    )

    fig.savefig(
        os.path.join(OUTPATH, f"singleProf{_num+1}_{_clim}.png"),
        bbox_inches="tight",
    )