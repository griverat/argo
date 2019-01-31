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
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
import os

class ArgoHist(object):

    def __init__(self, data, date1, date2, lats, lons):
        self.date1 = date1
        self.date2 = date2
        filt_data, x_grid, y_grid = filter_data(data, lats[0],
                                                lons[0], lats[1],
                                                lons[1], np.datetime64(self.date1),
                                                np.datetime64(self.date2))
        self.H, self.X, self.Y = self.get_histogram(filt_data, x_grid, y_grid)
        self.xi, self.yi, self.zi = self.get_kde(filt_data, self.H)
        self.proj = ccrs.PlateCarree(central_longitude=180)
        self.setup_plot()


    def setup_plot(self):
        plt.style.use('seaborn-paper')
        self.fig, self.ax = plt.subplots(subplot_kw=dict(projection=self.proj),figsize=(24,12))
        self.ax.set_xticks(np.arange(0,360,5), crs=ccrs.PlateCarree())
        self.ax.set_yticks(np.arange(-90,90,2.5), crs=ccrs.PlateCarree())
        lon_formatter = LongitudeFormatter(zero_direction_label=True)
        lat_formatter = LatitudeFormatter()
        self.ax.xaxis.set_major_formatter(lon_formatter)
        self.ax.yaxis.set_major_formatter(lat_formatter)
        self.ax.set_extent([70, 110, -20, 10], crs=self.proj)


    def get_histogram(self,filt_data, x_grid, y_grid):
        H, xedges, yedges = np.histogram2d(filt_data['lon'],
                                            filt_data['lat'],
                                            bins=(x_grid, y_grid))
        H = H.T
        X, Y = np.meshgrid(xedges, yedges)
        return H, X, Y


    def get_kde(self, filt_data, H):
        x = filt_data['lon'].values
        y = filt_data['lat'].values
        k = gaussian_kde(np.vstack([x, y]))
        xi, yi = np.mgrid[x.min():x.max():H.shape[1]*1j,y.min():y.max():H.shape[0]*1j]
        zi = k(np.vstack([xi.flatten(), yi.flatten()]))
        return xi, yi, zi


    def custom_cmap(self):
        cmap = plt.get_cmap('pink_r',8)
        cmaplist = [cmap(i) for i in range(cmap.N)]
        for j in range(len(cmaplist)):
            cmaplist[j] = (1.,1.,1.,0)
        cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)
        return cmap


    def plot(self):
        hq_border = cfeature.NaturalEarthFeature(
                                    category='cultural',
                                    name='admin_0_countries',
                                    scale='50m',
                                    facecolor=cfeature.COLORS['land'],
                                    edgecolor='black')
        self.ax.add_feature(hq_border)
        draw = self.ax.pcolormesh(self.X, self.Y, self.H,edgecolor='w',
                                    lw=0.004,transform=ccrs.PlateCarree(),
                                    cmap=plt.get_cmap('Blues',10))
        self.ax.contour(self.xi, self.yi, self.zi.reshape(self.xi.shape),
                        levels=8,transform=ccrs.PlateCarree(),
                        cmap=plt.get_cmap('pink_r',8),
                        linewidths=np.linspace(0,3,8))
        cmap = self.custom_cmap()
        cs = self.ax.contourf(self.xi, self.yi, self.zi.reshape(self.xi.shape),
                                transform=ccrs.PlateCarree(), cmap=cmap, 
                                hatches=[None,None,None,None,None,'\\\\', '//','--'])
        artists, labels = cs.legend_elements()
        del labels
        self.ax.legend(artists[-3:],['','',''], handleheight=2, 
                        title='High density',fancybox=True,fontsize='large')

        cbar = plt.colorbar(draw, ticks = np.arange(np.min(self.H),np.max(self.H),10))
        cbar.ax.tick_params(labelsize=15) 

        self.ax.tick_params(labelsize='medium')
        self.ax.set_title('2D histogram of ARGO data with density contours computed\n using a gaussian kernel density estimator\n({} - {})'.format(self.date1,self.date2),size=20)
        
    def show(self, output):
        plt.show()
        self.fig.savefig(os.path.join(output, 'hist+kde_argo.png'), dpi=400)

def load_data(filename):
    data = pd.read_csv(filename)
    data['date'] = pd.to_datetime(data['date'])
    return data

def filter_data(data, min_lat, min_lon, max_lat, max_lon,time1, time2):
    max_lat = max_lat
    max_lon = max_lon+1
    filt = data[(data['date']>time1)&(data['date']<time2)]
    filt = filt[(filt['lat']>min_lat)&(filt['lat']<max_lat)]
    filt = filt[(filt['lon']>min_lon)&(filt['lon']<max_lon)]
    x_grid = np.arange(min_lon,max_lon,0.5)
    y_grid = np.arange(min_lat,max_lat,0.5)
    return filt, x_grid, y_grid

if __name__ == '__main__':
    date1 = "1999-01-01"
    date2 = '2019-12-31'
    data = load_data('../Notebooks/Output/latlontemp.txt')
    hist = ArgoHist(data, date1, date2, [-20,10.5], [250,300])
    hist.plot()
    hist.show('/home/grivera/GitLab/argo/Histogram/Output')