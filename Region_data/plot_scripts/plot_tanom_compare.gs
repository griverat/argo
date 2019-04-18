'reinit'
'set display color white'
'c'
'set grads off'
'rgbset2'

outdir='../Output/'
name='argo_anomcomp'

time1='16apr2018'
time2='16apr2019'

**********
'xdfopen /data/users/grivera/GODAS/clim/godas_dayclim.ctl'
'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_252.5,259.0_-2.0,2.0.nc'
'sdfopen /data/users/grivera/ARGO-patch/argo_temp_252.5,259.0_-2.0,2.0.nc'
'set lev 5 200'
'set time 'time1' 'time2
'set dfile 2'
'set x 1'
'set y 1'
'define tsuav1 = ave(tanom.2,t-3,t+3)'
'define temp1 = ave(temp.3,t-4,t+4)'
'set dfile 1'
'define clim1 = aave(pottmp.1-273,lon=252.5,lon=259,lat=-2,lat=2)'
'close 3'
'close 2'

**********
'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_262.5,268.5_-2.0,2.0.nc'
'sdfopen /data/users/grivera/ARGO-patch/argo_temp_262.5,268.5_-2.0,2.0.nc'
'set lev 5 200'
'set time 'time1' 'time2
'set dfile 2'
'set x 1'
'set y 1'
'define tsuav2 = ave(tanom.2,t-3,t+3)'
'define temp2 = ave(temp.3,t-4,t+4)'
'set dfile 1'
'define clim2 = aave(pottmp.1-273,lon=262.5,lon=268.5,lat=-2,lat=2)'
'close 3'
'close 2'

**********
'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_270.0,280.0_-10.0,0.0.nc'
'sdfopen /data/users/grivera/ARGO-patch/argo_temp_270.0,280.0_-10.0,0.0.nc'
'set lev 5 200'
'set time 'time1' 'time2
'set dfile 2'
'set x 1'
'set y 1'
'define tsuav3 = ave(tanom.2,t-3,t+3)'
'define temp3 = ave(temp.3,t-4,t+4)'
'set dfile 1'
'define clim3 = aave(pottmp.1-273,lon=270,lon=280,lat=-10,lat=0)'


opt='0.3 0.8 0.7 2 0.4'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

************
'subplot 3 1 1 'opt
'set clevs 'clev
'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'd tsuav1'

'set gxout contour'
'set clab off'
'set clevs 'clev
'set ccolor 1'
'set cthick 1'
'd tsuav1'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd temp1'


'set ccolor 1'
'set clevs 20'
'set cthick 4'
'set clab off'
'd clim1'

'set strsiz 0.1 0.12'
'set string 1 c 2'
'draw string 5.5 8.05 a) Lon: [107.5W,101.0W]  Lat: [2.0S,2.0N]'

************
'subplot 3 1 2 'opt
'set clevs 'clev
'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'd tsuav2'

'set gxout contour'
'set clab off'
'set clevs 'clev
'set ccolor 1'
'set cthick 1'
'd tsuav2'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd temp2'

'set ccolor 1'
'set clevs 20'
'set cthick 4'
'set clab off'
'd clim2'

'set strsiz 0.1 0.12'
'set string 1 c 2'
'draw string 5.5 5.55 b) Lon: [97.5W,91.5W]  Lat: [2.0S,2.0N]'

************
'subplot 3 1 3 'opt
'set clevs 'clev
'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'd tsuav3'

'set gxout contour'
'set clab off'
'set clevs 'clev
'set ccolor 1'
'set cthick 1'
'd tsuav3'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd temp3'

'set ccolor 1'
'set clevs 20'
'set cthick 4'
'set clab off'
'd clim3'

'set strsiz 0.1 0.12'
'set string 1 c 2'
'draw string 5.5 3.05 c) Lon: [90.0W,80.0W]  Lat: [10.0S,0.]'

'cbarn'
************
'gxprint 'outdir''name'.eps'
'gxprint 'outdir''name'.png'
