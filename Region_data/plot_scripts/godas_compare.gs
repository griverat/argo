
'reinit'
'set display color white'
'c'

'set grads off'
'rgbset2'

opt='0.8 0.5 0.9 0.7 0.5 0.3'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'


'open /data/datos/godas/pentadas/godas_pentad_tgrid.ctl'
'sdfopen /data/users/grivera/GODAS/clim/daily/godas_dayclim.nc'
'set lev 0 200'
'set time 04apr2018 04apr2019'
*SUR
'profs=aave(potdsl.1,lon=257,lon=263,lat=-6,lat=-4) - 273'
'clims=aave(pottmp.2,lon=257,lon=263,lat=-6,lat=-4) - 273'
'anoms=profs-clims'
*NORTE 261.5,267.5_5.5,10.0
'profn=aave(potdsl.1,lon=257,lon=263,lat=4,lat=6) - 273'
'climn=aave(pottmp.2,lon=257,lon=263,lat=4,lat=6) - 273'
'anomn=profn-climn'

'set lon 260'
'set lat -5'
'set yflip on'

**************
'subplot 6 1 1 'opt
'set gxout shaded'
'set yflip on'
'd clims'

'set gxout contour'
'set ccols 1'
'd clims'

**************
'subplot 6 1 2 'opt
'set gxout shaded'
'set yflip on'
'd profs'

'set gxout contour'
'set ccols 1'
'd profs'

**************
'subplot 6 1 3 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd anoms'

'set gxout contour'
'set clevs 'clev
'set ccols 1'
'd anoms'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd profs'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set cstyle 2'
'set clab masked'
'd clims'


**************
'subplot 6 1 4 'opt
'set gxout shaded'
'set yflip on'
'd climn'

'set gxout contour'
'set ccols 1'
'd climn'

**************
'subplot 6 1 5 'opt
'set gxout shaded'
'set yflip on'
'd profn'

'set gxout contour'
'set ccols 1'
'd profn'

**************
'subplot 6 1 6 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd anomn'

'set gxout contour'
'set clevs 'clev
'set ccols 1'
'd anomn'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set clab masked'
'd profn'

'set ccolor 1'
'set clevs 20'
'set cthick 6'
'set cstyle 2'
'set clab masked'
'd climn'

