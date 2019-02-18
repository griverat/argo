'reinit'
'set display color white'
'c'
'rgbset2'

name='argo_temp'

'sdfopen /data/users/grivera/ARGO-patch/argo_temp_256.5-0.0.nc'

'set lev 0 300'
'set time 01oct2018 18feb2019'
'define tsuav = ave(temp,t-1,t+1)'

opt='0.4 0.3 0.3 0.4 0.4'

'subplot 1 2 1 'opt
'set yflip on'
'set gxout shaded'
'd temp'
'set gxout contour'
'set ccolor 1'
'd temp'

'subplot 1 2 2 'opt
'set yflip on'
'set gxout shaded'
'd tsuav'
'set gxout contour'
'set ccolor 1'
'd tsuav'

'print 'name'.eps'
