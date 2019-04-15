'reinit'
'set display color white'
'c'
'set grads off'
'rgbset2'

outdir='../Output/'
name='argo_anomcount'

time1='15apr2018'
time2='15apr2019'

*SUR
'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_258.0,262.5_-7.5,-4.0.nc'
'sdfopen /data/users/grivera/ARGO-patch/argo_temp_258.0,262.5_-7.5,-4.0.nc'

*NORTE
*'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_261.5,267.5_5.5,10.0.nc'
*'sdfopen /data/users/grivera/ARGO-patch/argo_temp_261.5,267.5_5.5,10.0.nc'

*argo_tanom_261.5,267.5_5.5,10.0.nc'
*argo_tanom_258.0,262.5_-7.5,-4.0.nc'
'set lev 0 200'
'set time 'time1' 'time2
'define tsuav = ave(tanom.1,t-2,t+2)'
'define tempsv = ave(temp.2,t-2,t+2)'

opt='0.8 0.5 0.9 1.4 0.5 0.4'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

************
'subplot 4 1 1 'opt
'set lev 0'
'set ylint 1'
'set gxout bar'
'd prof_count'

************
'subplot 4 1 2 'opt
'set lev 0 200'
*'set clevs 'clev
*'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'define clim=ave(tempsv-tsuav,t-3,t+3)'
'd clim'

'set gxout contour'
*'set clab off'
*'set clevs 'clev
*'set ccolor 1'
'set cthick 1'
'd clim'

************
'subplot 4 1 3 'opt
'set lev 0 200'
*'set clevs 'clev
*'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'd tempsv'

'set gxout contour'
*'set clab off'
*'set clevs 'clev
*'set ccolor 1'
'set cthick 1'
'd tempsv'

************
'subplot 4 1 4 'opt
'set lev 0 200'
'set clevs 'clev
'set ccols 'ccols
'set yflip on'
'set gxout grfill'
'd tsuav'

'set gxout contour'
'set clab off'
'set clevs 'clev
'set ccolor 1'
'set cthick 1'

'd tsuav'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'define temp2=ave(tempsv,t-5,t+5)'
'd temp2'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set cstyle 2'
'set clab masked'
'd clim'

'cbarn 0.8'
************
'gxprint 'outdir''name'.eps'
