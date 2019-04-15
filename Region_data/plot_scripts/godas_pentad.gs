
'reinit'
'set display color white'
'c'

'set grads off'
'rgbset2'

opt='0.8 0.6 0.9 0.8 0.5'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'


'open /data/datos/godas/pentadas/godas_pentad_tgrid.ctl'
'sdfopen /data/users/grivera/GODAS/clim/daily/godas_dayclim.nc'
'set lev 0 200'
'set time 08apr2018 08apr2019'
*SUR
*'prof=aave(potdsl.1,lon=258,lon=262.5,lat=-7.5,lat=-4) - 273'
*'clim=aave(pottmp.2,lon=258,lon=262.5,lat=-7.5,lat=-4) - 273'
*NORTE 261.5,267.5_5.5,10.0
'prof=aave(potdsl.1,lon=261.5,lon=267.5,lat=5.5,lat=10) - 273'
'clim=aave(pottmp.2,lon=261.5,lon=267.5,lat=5.5,lat=10) - 273'

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


