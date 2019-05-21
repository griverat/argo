'reinit'
'set display color white'
'c'
'set grads off'
'rgbset2'

outdir='../Output/'
name='prof3901231'
iso=16

opt='0.3 0.8 0.7 2 0.4'
clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

'sdfopen /data/users/grivera/ARGO-prof/3901231_imarpe.nc'

'set t last'
'q dims'
timeinfo=sublin(result,5)
timefnum=subwrd(timeinfo,9)
dateinfo=subwrd(timeinfo,6)
datef=substr(dateinfo,4,9)

'set t 'timefnum-365
'q dims'
timeinfo=sublin(result,5)
timeinum=subwrd(timeinfo,9)
dateinfo=subwrd(timeinfo,6)
datei=substr(dateinfo,4,9)
*******************

'set time 'datei' 'datef
'set lev 0 500'
'set x 1'
'set y 1'

'define tsuav = ave(temp_anom,t-5,t+5)'
'tsuav = ave(tsuav,t-5,t+5)'

'define temp = ave(temperature.1,t-5,t+5)'
'temp = ave(temp,t-5,t+5)'

'subplot 1 1 1 'opt
'set gxout shaded'
'set yflip on'
'set clevs 'clev
'set ccols 'ccols
'd tsuav'

'set gxout contour'
'set clevs 'clev
'set cthick 1'
'd tsuav'

'set gxout contour'
'set ccolor 1'
'set clevs 'iso
'set cthick 6'
'set clab masked'
'd temp'

'cbarn'


'set strsiz 0.15 0.2'
'set string 1 c 2'
'draw string 5.5 8.14 ARGO Profiler #3901231'

'set strsiz 0.1 0.1'
'set string 1 c 2'
'draw string 5.5 0.6 Latest data: 'datef

************
'gxprint 'outdir''name'.eps'
'gxprint 'outdir''name'.png'

