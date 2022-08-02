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
from dmelon.ocean.argo import build_dl, launch_shell
from geopandas.tools import sjoin


def findPointsInPolys(pandas_df, shape_df):
    # Create GeoDataFrame from pandas dataframe
    argo_geodf = gpd.GeoDataFrame(
        pandas_df,
        geometry=gpd.points_from_xy(
            pandas_df.longitude, pandas_df.latitude, crs="EPSG:4326"
        ),
    )

    # Make spatial join to filer out values outside the shapefile
    pointInPolys = sjoin(argo_geodf, shape_df, op="within", how="inner")
    return pointInPolys


def maskVariableShape(variable, shape):
    return variable.where(
        shape.mask(variable.sel(lat=slice(-20, 0), lon=slice(-90, -70))) == 0
    )


# godas_clim = xr.open_dataset("godas_clim_month.nc").pottmp
# godas_zero = godas_clim.isel(level=0)
# godas_zero["level"] = 0
# godas_clim = xr.concat([godas_zero, godas_clim], dim="level")
# godas_clim


import cmocean as cmo

# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import regionmask

# from dmelon.plotting import HQ_BORDER, format_latlon

### PLOT ###
def makePlot(
    psal,
    psal_raw,
    temp,
    temp_raw,
    sla,
    taux,
    tauy,
    ssta,
    latest_date,
    out_path="",
    depth=850,
):
    fig = plt.figure(constrained_layout=True, figsize=(8, 8), dpi=300)
    spec = gridspec.GridSpec(ncols=1, nrows=4, figure=fig, height_ratios=[1, 1, 2, 2])
    f_ax0 = fig.add_subplot(spec[3, :])
    f_ax1 = fig.add_subplot(spec[2, :], sharex=f_ax0)
    f_ax2 = fig.add_subplot(spec[1, :], sharex=f_ax0)
    f_ax3 = fig.add_subplot(spec[0, :], sharex=f_ax0)

    ### SAL
    plot_data_smooth = (
        psal.interpolate_na(dim="LATITUDE")
        .rolling(LATITUDE=5, center=True, min_periods=1)
        .mean()
    )
    plot_data_smooth.plot.contourf(
        x="LATITUDE",
        vmin=33.5,
        vmax=35.1,
        cmap=cmo.cm.haline,
        levels=33,
        ax=f_ax0,
        yincrease=False,
        cbar_kwargs=dict(label="Salinity", pad=-0.09, ticks=np.arange(33.5, 35.2, 0.2)),
    )
    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        vmin=33.5,
        vmax=35.1,
        levels=17,
        ax=f_ax0,
        colors="k",
        linewidths=0.2,
        yincrease=False,
    )

    lev = conts.levels.copy()
    lev = lev[lev != 34.9]
    f_ax0.clabel(conts, levels=lev, fontsize=7, inline_spacing=-7)

    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        levels=[33.8, 34.8, 35.1],
        ax=f_ax0,
        colors="k",
        linewidths=0.8,
        yincrease=False,
    )

    f_ax0.clabel(conts, fontsize=6.73, inline=True, inline_spacing=-7)

    f_ax0.scatter(
        psal_raw.LATITUDE,
        np.full_like(psal_raw.LATITUDE, 0),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax0.scatter(
        psal_raw.LATITUDE,
        np.full_like(psal_raw.LATITUDE, depth),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax0.set_xlim(-20, -2)
    f_ax0.set_ylim(depth, 0)
    f_ax0.set_ylabel("Depth [m]")
    f_ax0.set_xlabel("Latitude")
    f_ax0.grid(ls="--", alpha=0.5)

    ### TEMP

    plot_data_smooth = (
        temp.interpolate_na(dim="LATITUDE")
        .rolling(LATITUDE=5, center=True, min_periods=1)
        .mean()
    )
    plot_data_smooth.plot.contourf(
        x="LATITUDE",
        vmin=4,
        vmax=25,
        cmap=cmo.cm.thermal,
        levels=22,
        ax=f_ax1,
        yincrease=False,
        cbar_kwargs=dict(label="Temperature [°C]", pad=-0.09),
    )
    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        vmin=4,
        vmax=25,
        levels=22,
        ax=f_ax1,
        colors="k",
        linewidths=0.2,
        yincrease=False,
    )

    # conts = plot_data_smooth.plot.contour(
    #     x="LATITUDE",
    #     vmin=14,
    #     vmax=29,
    #     levels=[0],
    #     ax=f_ax1,
    #     colors="k",
    #     linewidths=1,
    #     yincrease=False,
    # )

    f_ax1.clabel(conts)

    f_ax1.scatter(
        temp_raw.LATITUDE,
        np.full_like(temp_raw.LATITUDE, 0),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax1.scatter(
        temp_raw.LATITUDE,
        np.full_like(temp_raw.LATITUDE, depth),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax1.set_ylim(depth, 0)
    f_ax1.set_ylabel("Depth [m]")
    f_ax1.set_xlabel("Latitude")
    f_ax1.grid(ls="--", alpha=0.5)

    ### REST
    (sla.mean(dim=["time", "lon"]) * 100).plot(ax=f_ax2)
    f_ax2.axhline(ls="--", c="k", lw=0.5)
    f_ax2.set_yticks(np.arange(-5, 5.1, 2))
    f_ax2.set_ylim(-5, 5)
    f_ax2.set_ylabel("SLA [cm]")
    f_ax2.set_xlabel("Latitude")

    Q = f_ax2.quiver(
        taux.lat[::2],
        np.full_like(taux.lat, 0)[::2],
        tauy.mean(dim=["time", "lon"])[::2] * 100,
        taux.mean(dim=["time", "lon"])[::2] * -100,
        units="xy",
        scale_units="xy",
        scale=1,
        width=0.05,
    )
    f_ax2.quiverkey(
        Q,
        0.92,
        0.85,
        1,
        r"$1x10^{-2} \frac{N}{m^2}$",
        labelpos="E",
        coordinates="axes",
        fontproperties=dict(size=7),
        labelsep=0.02,
    )

    f_ax2.text(0.885, 0.885, r"$\tau$", transform=f_ax2.transAxes)
    f_ax2.grid(ls="--", alpha=0.5)

    card_centerx = 1.06
    card_centery = 0.5
    da = 0.04
    arrowprops = dict(arrowstyle="fancy", facecolor="black")

    f_ax2.annotate(
        "",
        xy=(card_centerx + da, card_centery),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx - da, card_centery),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx, card_centery + da * 7),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx, card_centery - da * 7),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.text(
        card_centerx + da,
        card_centery,
        "N",
        transform=f_ax2.transAxes,
        va="center",
        ha="left",
    )
    f_ax2.text(
        card_centerx - da,
        card_centery,
        "S",
        transform=f_ax2.transAxes,
        va="center",
        ha="right",
    )
    f_ax2.text(
        card_centerx,
        card_centery + da * 7,
        "W",
        transform=f_ax2.transAxes,
        va="bottom",
        ha="center",
    )
    f_ax2.text(
        card_centerx,
        card_centery - da * 7,
        "E",
        transform=f_ax2.transAxes,
        va="top",
        ha="center",
    )

    ssta.mean(dim=["time", "lon"]).rolling(
        lat=10, min_periods=1, center=True
    ).mean().plot(ax=f_ax3)
    f_ax3.set_ylabel("SSTA [°C]")
    f_ax3.set_xlabel("Latitude")
    f_ax3.set_yticks(np.arange(-3.5, 3.51, 1))
    f_ax3.set_ylim(-3.5, 3.5)
    f_ax3.axhline(ls="--", c="k", lw=0.5)
    f_ax3.grid(ls="--", alpha=0.5)

    props = dict(boxstyle="round", facecolor="wheat", alpha=0.2)
    f_ax0.text(
        0.03,
        0.95,
        "d",
        transform=f_ax0.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax1.text(
        0.03,
        0.95,
        "c",
        transform=f_ax1.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax2.text(
        0.03,
        0.9,
        "b",
        transform=f_ax2.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax3.text(
        0.03,
        0.9,
        "a",
        transform=f_ax3.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )

    f_ax3.text(
        0,
        1.65,
        "[a] OSTIA Sea Surface Temperature Anomaly\n"
        "[b] (Line) DUACS L4 Sea Level Anomaly\n"
        "     (Arrows) ASCAT L3 Wind Stress Anomaly",
        transform=f_ax3.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )

    f_ax3.text(
        0.6,
        1.65,
        "Clim: GODAS      1981-2010\n"
        "Clim: DUACS L4  1993-2010\n"
        "Clim: ASCAT - ERA adjusted 2008-2014\n",
        transform=f_ax3.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )

    f_ax0.text(
        0,
        -0.3,
        "[c] ARGO Vertical Temperature\n" "[d] ARGO Vertical Practical Salinity",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )
    # f_ax0.text(
    #     0.6,
    #     -0.3,
    #     "Clim: IMARPE      1981-2020",
    #     transform=f_ax0.transAxes,
    #     verticalalignment="top",
    #     horizontalalignment="left",
    # )

    f_ax0.text(
        0,
        -0.15,
        "Processing: IGP",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
        fontsize=9,
    )

    f_ax0.text(
        1,
        -0.15,
        f"Latest Date: {pd.to_datetime(latest_date.data):%d-%b-%Y}",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        fontsize=9,
    )

    f_ax0.text(
        1,
        -0.4,
        f"*All plots shown are 30-day average of data points\n within 200nm from the coast",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        fontsize=9,
    )

    fig.savefig(os.path.join(out_path, f"CoastMVar200nm_{depth}.png"))
    fig.savefig(os.path.join(out_path, f"CoastMVar200nm_{depth}.jpeg"), dpi=200)


### PLOT ANOM ###
def makePlot_anom(
    psal,
    psal_raw,
    temp,
    temp_raw,
    sla,
    taux,
    tauy,
    ssta,
    latest_date,
    out_path="",
    depth=850,
):
    fig = plt.figure(constrained_layout=True, figsize=(8, 8), dpi=300)
    spec = gridspec.GridSpec(ncols=1, nrows=4, figure=fig, height_ratios=[1, 1, 2, 2])
    f_ax0 = fig.add_subplot(spec[3, :])
    f_ax1 = fig.add_subplot(spec[2, :], sharex=f_ax0)
    f_ax2 = fig.add_subplot(spec[1, :], sharex=f_ax0)
    f_ax3 = fig.add_subplot(spec[0, :], sharex=f_ax0)

    ### SAL
    plot_data_smooth = (
        psal.interpolate_na(dim="LATITUDE")
        .rolling(LATITUDE=5, center=True, min_periods=1)
        .mean()
    )
    plot_data_smooth.plot.contourf(
        x="LATITUDE",
        vmin=33.5,
        vmax=35.1,
        cmap=cmo.cm.haline,
        levels=33,
        ax=f_ax0,
        yincrease=False,
        cbar_kwargs=dict(label="Salinity", pad=-0.09, ticks=np.arange(33.5, 35.2, 0.2)),
    )
    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        vmin=33.5,
        vmax=35.1,
        levels=17,
        ax=f_ax0,
        colors="k",
        linewidths=0.2,
        yincrease=False,
    )

    lev = conts.levels.copy()
    lev = lev[lev != 34.9]
    f_ax0.clabel(conts, levels=lev, fontsize=7, inline_spacing=-7)

    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        levels=[33.8, 34.8, 35.1],
        ax=f_ax0,
        colors="k",
        linewidths=0.8,
        yincrease=False,
    )

    f_ax0.clabel(conts, fontsize=6.73, inline=True, inline_spacing=-7)

    f_ax0.scatter(
        psal_raw.LATITUDE,
        np.full_like(psal_raw.LATITUDE, 0),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax0.scatter(
        psal_raw.LATITUDE,
        np.full_like(psal_raw.LATITUDE, depth),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax0.set_xlim(-20, -2)
    f_ax0.set_ylim(depth, 0)
    f_ax0.set_ylabel("Depth [m]")
    f_ax0.set_xlabel("Latitude")
    f_ax0.grid(ls="--", alpha=0.5)

    ### TEMP

    plot_data_smooth = (
        temp.interpolate_na(dim="LATITUDE")
        .rolling(LATITUDE=5, center=True, min_periods=1)
        .mean()
    )
    plot_data_smooth.plot.contourf(
        x="LATITUDE",
        vmin=-3,
        vmax=3,
        cmap="RdBu_r",
        levels=13,
        ax=f_ax1,
        yincrease=False,
        cbar_kwargs=dict(label="Temperature Anomaly [°C]", pad=-0.09),
    )
    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        vmin=-3,
        vmax=3,
        levels=13,
        ax=f_ax1,
        colors="k",
        linewidths=0.2,
        yincrease=False,
    )

    conts = plot_data_smooth.plot.contour(
        x="LATITUDE",
        vmin=-3,
        vmax=3,
        levels=[0],
        ax=f_ax1,
        colors="k",
        linewidths=1,
        yincrease=False,
    )

    f_ax1.clabel(conts)

    f_ax1.scatter(
        temp_raw.LATITUDE,
        np.full_like(temp_raw.LATITUDE, 0),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax1.scatter(
        temp_raw.LATITUDE,
        np.full_like(temp_raw.LATITUDE, depth),
        c="k",
        s=5,
        marker="s",
        clip_on=False,
    )

    f_ax1.set_ylim(depth, 0)
    f_ax1.set_ylabel("Depth [m]")
    f_ax1.set_xlabel("Latitude")
    f_ax1.grid(ls="--", alpha=0.5)

    ### REST
    (sla.mean(dim=["time", "lon"]) * 100).plot(ax=f_ax2)
    f_ax2.axhline(ls="--", c="k", lw=0.5)
    f_ax2.set_yticks(np.arange(-5, 5.1, 2))
    f_ax2.set_ylim(-5, 5)
    f_ax2.set_ylabel("SLA [cm]")
    f_ax2.set_xlabel("Latitude")

    Q = f_ax2.quiver(
        taux.lat[::2],
        np.full_like(taux.lat, 0)[::2],
        tauy.mean(dim=["time", "lon"])[::2] * 100,
        taux.mean(dim=["time", "lon"])[::2] * -100,
        units="xy",
        scale_units="xy",
        scale=1,
        width=0.05,
    )
    f_ax2.quiverkey(
        Q,
        0.92,
        0.85,
        1,
        r"$1x10^{-2} \frac{N}{m^2}$",
        labelpos="E",
        coordinates="axes",
        fontproperties=dict(size=7),
        labelsep=0.02,
    )

    f_ax2.text(0.885, 0.885, r"$\tau$", transform=f_ax2.transAxes)
    f_ax2.grid(ls="--", alpha=0.5)

    card_centerx = 1.06
    card_centery = 0.5
    da = 0.04
    arrowprops = dict(arrowstyle="fancy", facecolor="black")

    f_ax2.annotate(
        "",
        xy=(card_centerx + da, card_centery),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx - da, card_centery),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx, card_centery + da * 7),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.annotate(
        "",
        xy=(card_centerx, card_centery - da * 7),
        xytext=(card_centerx, card_centery),
        arrowprops=arrowprops,
        xycoords="axes fraction",
    )

    f_ax2.text(
        card_centerx + da,
        card_centery,
        "N",
        transform=f_ax2.transAxes,
        va="center",
        ha="left",
    )
    f_ax2.text(
        card_centerx - da,
        card_centery,
        "S",
        transform=f_ax2.transAxes,
        va="center",
        ha="right",
    )
    f_ax2.text(
        card_centerx,
        card_centery + da * 7,
        "W",
        transform=f_ax2.transAxes,
        va="bottom",
        ha="center",
    )
    f_ax2.text(
        card_centerx,
        card_centery - da * 7,
        "E",
        transform=f_ax2.transAxes,
        va="top",
        ha="center",
    )

    ssta.mean(dim=["time", "lon"]).rolling(
        lat=10, min_periods=1, center=True
    ).mean().plot(ax=f_ax3)
    f_ax3.set_ylabel("SSTA [°C]")
    f_ax3.set_xlabel("Latitude")
    f_ax3.set_yticks(np.arange(-3.5, 3.51, 1))
    f_ax3.set_ylim(-3.5, 3.5)
    f_ax3.axhline(ls="--", c="k", lw=0.5)
    f_ax3.grid(ls="--", alpha=0.5)

    props = dict(boxstyle="round", facecolor="wheat", alpha=0.2)
    f_ax0.text(
        0.03,
        0.95,
        "d",
        transform=f_ax0.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax1.text(
        0.03,
        0.95,
        "c",
        transform=f_ax1.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax2.text(
        0.03,
        0.9,
        "b",
        transform=f_ax2.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )
    f_ax3.text(
        0.03,
        0.9,
        "a",
        transform=f_ax3.transAxes,
        bbox=props,
        verticalalignment="top",
        horizontalalignment="right",
    )

    f_ax3.text(
        0,
        1.65,
        "[a] OSTIA Sea Surface Temperature Anomaly\n"
        "[b] (Line) DUACS L4 Sea Level Anomaly\n"
        "     (Arrows) ASCAT L3 Wind Stress Anomaly",
        transform=f_ax3.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )

    f_ax3.text(
        0.6,
        1.65,
        "Clim: GODAS      1981-2010\n"
        "Clim: DUACS L4  1993-2010\n"
        "Clim: ASCAT - ERA adjusted 2008-2014\n",
        transform=f_ax3.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )

    f_ax0.text(
        0,
        -0.3,
        "[c] ARGO Vertical Temperature Anomaly\n"
        "[d] ARGO Vertical Practical Salinity",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )
    f_ax0.text(
        0.6,
        -0.3,
        "Clim: IMARPE      1981-2020",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )

    f_ax0.text(
        0,
        -0.15,
        "Processing: IGP",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
        fontsize=9,
    )

    f_ax0.text(
        1,
        -0.15,
        f"Latest Date: {pd.to_datetime(latest_date.data):%d-%b-%Y}",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        fontsize=9,
    )

    f_ax0.text(
        1,
        -0.4,
        f"*All plots shown are 30-day average of data points\n within 200nm from the coast",
        transform=f_ax0.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        fontsize=9,
    )

    fig.savefig(os.path.join(out_path, f"CoastMVar200nm_anom_{depth}.png"))
    fig.savefig(os.path.join(out_path, f"CoastMVar200nm_anom_{depth}.jpeg"), dpi=200)


if __name__ == "__main__":

    ### LOAD DATASETS ###

    OUTPUT = "/data/users/service/ARGO/FLOATS/output/ARGO-plots"

    # Date and region bounds
    region = [-90, -70, -20, -2.5]
    today = datetime.datetime.today()
    idate = today - datetime.timedelta(days=30)
    endate = today + datetime.timedelta(days=15)
    date_range = [
        f"{idate:%Y-%m-%d}",
        f"{endate:%Y-%m-%d}",
    ]

    # Vertical Sea Temperature Climatology
    imarpe_clim = xr.open_dataset(
        "/data/users/grivera/IMARPE/MonthlyTSOClimatology.nc"
    ).temperature.rename(depth="level", latitude="lat", longitude="lon")

    godas_dayclim = (
        xr.open_mfdataset("/data/users/grivera/GODAS/clim/daily/202*.nc").pottmp
        - 273.15
    )
    godas_dayclim["lon"] = np.where(
        godas_dayclim["lon"] > 180, godas_dayclim["lon"] - 360, godas_dayclim["lon"]
    )
    godas_dayclim = godas_dayclim.sortby("lon")

    sla = (
        xr.open_mfdataset(
            "/data/datos/jason_duacs/nrt_data/grid_duacs_allsat_new/202*/*.nc"
        )
        .sla.rename(latitude="lat", longitude="lon")
        .load()
    )
    sla["lon"] = np.where(sla["lon"] > 180, sla["lon"] - 360, sla["lon"])
    sla = sla.sortby("lon")
    sla_ = sla.tail(time=365).mean("time")
    sla_ = (sla - sla_).sel(time=slice(idate, None))
    sla_

    ascat_tau_anom = xr.open_mfdataset("/data/datos/ASCAT/DATA_TAU_NC/*.nc")
    ascat_tau_anom["lon"] = np.where(
        ascat_tau_anom.lon > 180, ascat_tau_anom.lon - 360, ascat_tau_anom.lon
    )
    ascat_tau_anom = ascat_tau_anom.sortby("lon").sel(time=slice(idate, None))

    sst = (
        xr.open_mfdataset("/data/datos/ostia_sst/202*/*/*.nc").analysed_sst.sel(
            time=slice(idate, None)
        )
        - 273.15
    )

    # ARGOpy Global options
    argopy.set_options(src="localftp", local_ftp="/data/datos/ARGO/gdac")
    argopy.set_options(mode="expert")

    # Data Fetcher
    argo_loader = ArgoDataFetcher(parallel="process", progress=True)

    # Index Fetcher
    index_loader = ArgoIndexFetcher()

    # Load dataframe
    argo_df = (
        index_loader.region(region + date_range).to_dataframe().sort_values("date")
    )

    launch_shell(build_dl(argo_df))

    # Load profiles with xarray
    ds = argo_loader.region(region + [0, 1000] + date_range).to_xarray()

    ds_profile = ds.argo.point2profile().sortby("TIME")
    ds_profile["N_PROF"] = argo_df.index

    # Apply QC to variables of interest
    ds_profile_qc = ds_profile.copy()
    ds_profile_qc["PSAL"] = ds_profile.PSAL.where(ds_profile.PSAL_QC == 1)
    ds_profile_qc["TEMP"] = ds_profile.TEMP.where(ds_profile.TEMP_QC == 1)
    ds_profile_qc["PRES"] = ds_profile.PRES.where(ds_profile.PRES_QC == 1)

    # Read and mask with 200nm shapefile
    mask200 = gpd.read_file("/data/users/grivera/Shapes/NEW_MASK/200mn_full.shp")
    pointInPolys = findPointsInPolys(argo_df, mask200)

    buffer = regionmask.from_geopandas(mask200, name="buffer200")

    # Interpolate to standard levels
    level = np.arange(0, 900, 10)
    argo_interp = (
        ds_profile_qc[["TEMP", "PRES", "PSAL"]]
        .sel(N_PROF=pointInPolys.index)
        .dropna(dim="N_PROF", how="all")
        .argo.interp_std_levels(level)
    )

    CLIM = imarpe_clim

    _cont = []
    _cont_abs = []
    for temp_profile in argo_interp.TEMP:
        sel_clim = CLIM.sel(
            lat=temp_profile.LATITUDE,
            lon=temp_profile.LONGITUDE,
            month=temp_profile.TIME.dt.month,
            method="nearest",
            drop=True,
        )
        sel_clim_interp = sel_clim.interp(
            level=level, kwargs=dict(fill_value="extrapolate")
        )
        temp_profile["level"] = (
            gsw.z_from_p(temp_profile.PRES_INTERPOLATED, temp_profile.LATITUDE) * -1
        )
        temp_profile = temp_profile.swap_dims(PRES_INTERPOLATED="level").interp(
            level=level, kwargs=dict(fill_value="extrapolate")
        )
        anom = temp_profile - sel_clim
        _cont_abs.append(temp_profile)
        _cont.append(anom)

    temp_data_raw = (
        xr.concat(_cont, dim="LATITUDE").sortby("TIME").groupby("LATITUDE").mean()
    )
    temp_data_abs_raw = (
        xr.concat(_cont_abs, dim="LATITUDE").sortby("TIME").groupby("LATITUDE").mean()
    )

    temp_data = (
        temp_data_raw.groupby_bins(
            "LATITUDE", bins=np.arange(-20, 0.6, 0.1), labels=np.arange(-20, 0.5, 0.1)
        )
        .mean()
        .rename(LATITUDE_bins="LATITUDE")
    )
    temp_data_abs = (
        temp_data_abs_raw.groupby_bins(
            "LATITUDE", bins=np.arange(-20, 0.6, 0.1), labels=np.arange(-20, 0.5, 0.1)
        )
        .mean()
        .rename(LATITUDE_bins="LATITUDE")
    )

    _cont_psal = []
    for psal_profile in argo_interp.PSAL:
        psal_profile["level"] = (
            gsw.z_from_p(psal_profile.PRES_INTERPOLATED, psal_profile.LATITUDE) * -1
        )
        psal_profile = psal_profile.swap_dims(PRES_INTERPOLATED="level").interp(
            level=level, kwargs=dict(fill_value="extrapolate")
        )
        _cont_psal.append(psal_profile)

    psal_data_raw = (
        xr.concat(_cont_psal, dim="LATITUDE").sortby("TIME").groupby("LATITUDE").mean()
    )
    psal_data = (
        psal_data_raw.groupby_bins(
            "LATITUDE", bins=np.arange(-20, 0.6, 0.1), labels=np.arange(-20, 0.5, 0.1)
        )
        .mean()
        .rename(LATITUDE_bins="LATITUDE")
    )

    # PLOT READY DATA

    sla_plot = maskVariableShape(sla_, buffer)
    taux_plot = maskVariableShape(ascat_tau_anom.taux_anom, buffer)
    tauy_plot = maskVariableShape(ascat_tau_anom.tauy_anom, buffer)

    ssta_plot = maskVariableShape(sst, buffer)
    godas_dayclim_sel = godas_dayclim.isel(level=0, drop=True)
    ssta_plot = (ssta_plot - godas_dayclim_sel.interp_like(ssta_plot)).load()

    makePlot(
        psal_data,
        psal_data_raw,
        temp_data_abs,
        temp_data_abs_raw,
        sla_plot,
        taux_plot,
        tauy_plot,
        ssta_plot,
        argo_interp.TEMP.TIME.max(),
        out_path=OUTPUT,
        depth=200,
    )

    makePlot_anom(
        psal_data,
        psal_data_raw,
        temp_data,
        temp_data_raw,
        sla_plot,
        taux_plot,
        tauy_plot,
        ssta_plot,
        argo_interp.TEMP.TIME.max(),
        out_path=OUTPUT,
        depth=200,
    )

    makePlot(
        psal_data,
        psal_data_raw,
        temp_data_abs,
        temp_data_abs_raw,
        sla_plot,
        taux_plot,
        tauy_plot,
        ssta_plot,
        argo_interp.TEMP.TIME.max(),
        out_path=OUTPUT,
    )

    makePlot_anom(
        psal_data,
        psal_data_raw,
        temp_data,
        temp_data_raw,
        sla_plot,
        taux_plot,
        tauy_plot,
        ssta_plot,
        argo_interp.TEMP.TIME.max(),
        out_path=OUTPUT,
    )
