
'reinit'
'set display color white'
'c'

'set grads off'
'rgbset2'

opt='0.8 0.6 0.9 0.8 0.5'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

outdir='../Output/'
name='godas_naylamp'
lat='5S'

'open /data/datos/godas/pentadas/godas_pentad_tgrid.ctl'
'sdfopen /data/users/grivera/GODAS/clim/daily/godas_dayclim.nc'

'set t last'
'q dims'
timeinfo=sublin(result,5)
timefnum=subwrd(timeinfo,9)
dateinfo=subwrd(timeinfo,6)
datef=substr(dateinfo,4,9)

'set t 'timefnum-73
'q dims'
timeinfo=sublin(result,5)
timeinum=subwrd(timeinfo,9)
dateinfo=subwrd(timeinfo,6)
datei=substr(dateinfo,4,9)
*******************

'set time 'datei' 'datef

'set lev 0 200'
*NORTE
'prof=aave(potdsl.1,lon=263.5,lon=266.5,lat=-7.5,lat=-3.5) - 273'
'clim=aave(pottmp.2,lon=263.5,lon=266.5,lat=-7.5,lat=-3.5) - 273'
*SUR 261.5,267.5_5.5,10.0  -9.5 -6.5 263.5 266.5
*'prof=aave(potdsl.1,lon=263.5,lon=266.5,lat=-9.5,lat=-6.5) - 273'
*'clim=aave(pottmp.2,lon=263.5,lon=266.5,lat=-9.5,lat=-6.5) - 273'

'set lon 260'
'set lat -5'
'set yflip on'

**************
'subplot 3 1 1 'opt
'set gxout shaded'
'set yflip on'
'd clim'

'set gxout contour'
'set ccols 1'
'd clim'

**************
'subplot 3 1 2 'opt
'set gxout shaded'
'set yflip on'
'd prof'

'set gxout contour'
'set ccols 1'
'd prof'

**************
'subplot 3 1 3 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd prof-clim'

'set gxout contour'
'set clevs 'clev
'set ccols 1'
'd prof-clim'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd prof'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set cstyle 2'
'set clab masked'
'd clim'

'set strsiz 0.093 0.1'
'set string 1 l 3'
'draw string 0.6 8 Source: GODAS   Processing: IGP   Latest pentad: 'datef

'set strsiz 0.093 0.1'
'set string 1 r 3'
'draw string 10.5 8 3`3.`0 box mean centered on 'lat' - 85`3.`0W'

'gxprint 'outdir''name'_'lat'.eps'
