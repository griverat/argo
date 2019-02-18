'reinit'
'set display color white'
'c'
'rgbset2'

name='argo_anom'

'sdfopen /data/users/grivera/ARGO-patch/argo_tanom_256.5-0.0.nc'

'set lev 0 300'
'set time 01oct2018 18feb2019'
'define tsuav = ave(tanom,t-1,t+1)'

opt='0.4 0.3 0.3 0.4 0.4'

'subplot 1 2 1 'opt
'set yflip on'
'set gxout shaded'
'd tanom'
'set gxout contour'
'set ccolor 1'
'd tanom'

'subplot 1 2 2 'opt
'set yflip on'
'set gxout shaded'
'd tsuav'
'set gxout contour'
'set ccolor 1'
'd tsuav'

'print 'name'.eps'
