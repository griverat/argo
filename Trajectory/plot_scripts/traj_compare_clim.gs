'reinit'
'set display color white'
'c'
'set grads off'
'rgbset2'

outdir='../Output/'
name='prof3901231_paita_clim'

time1='21apr2018'
time2='21apr2019'

opt='0.3 0.6 0.7 2 0.4'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

'sdfopen /data/users/grivera/ARGO-prof/3901231_paita_godas.nc'
'sdfopen /data/users/grivera/ARGO-prof/3901231_paita_soda.nc'
'sdfopen /data/users/grivera/ARGO-prof/3901231_paita_imarpe.nc'

'set x 1'
'set y 1'
'set t last'
'q dims'
tt5=sublin(result,5)
tf5=subwrd(tt5,6)
date=substr(tf5,4,9)

'set time 'time1' 'time2
*'set t 1 last'
'set lev 0 500'

****************
'tsuav = ave(temp_anom.1,t-5,t+5)'
'tsuav = ave(tsuav,t-5,t+5)'

'subplot 3 1 1 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd tsuav'

'set gxout contour'
'set clevs 'clev
'set cthick 1'
'd tsuav'


****************
'tsuav = ave(temp_anom.2,t-5,t+5)'
'tsuav = ave(tsuav,t-5,t+5)'

'subplot 3 1 2 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd tsuav'

'set gxout contour'
'set clevs 'clev
'set cthick 1'
'd tsuav'


****************
'tsuav = ave(temp_anom.3,t-5,t+5)'
'tsuav = ave(tsuav,t-5,t+5)'

'subplot 3 1 3 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd tsuav'

'set gxout contour'
'set clevs 'clev
'set cthick 1'
'd tsuav'


'cbarn 1 0 5.5 0.25'


'set strsiz 0.15 0.2'
'set string 1 c 5'
'draw string 5.5 8.14 ARGO Profiler #3901231'

'set strsiz 0.093 0.1'
'set string 1 l 6'
'draw string 0.5 7.75 a)'
'draw string 0.5 5.3 b)'
'draw string 0.5 2.85 c)'

'set strsiz 0.093 0.1'
'set string 1 l 3'
'draw string 1.07 0.55 Source: ARGO GDAC   Processing: IGP   Clim: 1981-2010 - a)GODAS, b)SODA, c)IMARPE   Latest data: 'date

************
'gxprint 'outdir''name'.eps'
'gxprint 'outdir''name'.png'

