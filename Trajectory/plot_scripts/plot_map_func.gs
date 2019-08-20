function main(args)
    'reinit'
    say args
    if ( args='?' )
        say 'This script needs 6 arguments: profcode lat1 lat2 lon1 lon2 profout'
        return
    else
        profcode=subwrd(args,1)
        maplat1=subwrd(args,2)
        maplat2=subwrd(args,3)
        maplon1=subwrd(args,4)
        maplon2=subwrd(args,5)
        profout=subwrd(args,6)
    endif

    say "profcode set to: "profcode
    say "maplat1 set to: "maplat1
    say "maplat2 set to: "maplat2
    say "maplon1 set to: "maplon1
    say "maplon2 set to: "maplon2
    say "profout set to: "profout

    'set warn off'
    'set display color white'
    'c'
    'set grads off'
    'rgbset2'

    outdir='../Output/'profcode'/'
    name='prof'profcode'_clim_trajr'

    iso=16

    opt='0.8 0.6 0.8 2 0.6 0.8'
    clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
    ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'
    cols= '6 2 8 12 7 10 3 13 5 11 4 14 9'
    colstraj='9 14 4 11 5 13 3 10 7 12 8 2 6'

    'sdfopen 'profout'/'profcode'_godas.nc'
    'sdfopen 'profout'/'profcode'_soda.nc'
    'sdfopen 'profout'/'profcode'_imarpe.nc'
    'xdfopen /data/users/grivera/GODAS/clim/godas_dayclim.ctl'

***************
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

*********************************
    'define tsuav = ave(temp_anom.1,t-5,t+5)'
    'tsuav = ave(tsuav,t-5,t+5)'
    'define temp = ave(temperature.1,t-5,t+5)'
    'temp = ave(temp,t-5,t+5)'

    'subplot 3 2 1 'opt
    'set gxout shaded'
    'set yflip on'
    'set clevs 'clev
    'set ccols 'ccols
    'd tsuav'

    'set gxout contour'
    'set clevs 'clev
    'set cthick 1'
    'd tsuav'

    'set ccolor 1'
    'set clevs 'iso
    'set cthick 6'
    'set clab masked'
    'd temp'

    t0=datef
    y0=500
    'q w2xy 't0' 'y0
    xf=subwrd(result,3); yf=subwrd(result,6)

    ncol=1
    timefnum_=timefnum
    while (timeinum < timefnum_)
        'set line 'subwrd(cols,ncol)' 1 12'
        timefnum_=timefnum_-30
        if (timefnum_ < timeinum)
            timefnum_=timeinum
        endif
        'set t 'timefnum_
        'q time'
        dateinfo=subwrd(result,3)
        daten=substr(dateinfo,4,9)
        'q w2xy 'daten' 'y0
        xi=subwrd(result,3); yi=subwrd(result,6)
        'drawpoly 'xi' 'yf' 'xf' 'yf
        xf=xi; yf=yi; ncol=ncol+1
    endwhile

    status=0
    'set line 1 1 5'
    while (status != 2)
        marks = read(''profout'/'profcode'-traj1.txt')
        status = subwrd(marks,1)
        if (status=2)
            break
        endif
        datepoint=subwrd(marks,6)
        'q w2xy 'datepoint' 500'
        xi=subwrd(result,3); yi=subwrd(result,6)
        'draw mark 4 'xi' 'yi' 0.05'
    endwhile

*********************************
    'set time 'datei' 'datef
    'define tsuav = ave(temp_anom.2,t-5,t+5)'
    'tsuav = ave(tsuav,t-5,t+5)'
    'define temp = ave(temperature.2,t-5,t+5)'
    'temp = ave(temp,t-5,t+5)'

    'subplot 3 2 3 'opt
    'set gxout shaded'
    'set yflip on'
    'set clevs 'clev
    'set ccols 'ccols
    'd tsuav'

    'set gxout contour'
    'set clevs 'clev
    'set cthick 1'
    'd tsuav'

    'set ccolor 1'
    'set clevs 'iso
    'set cthick 6'
    'set clab masked'
    'd temp'

    t0=datef
    y0=500
    'q w2xy 't0' 'y0
    xf=subwrd(result,3); yf=subwrd(result,6)

    ncol=1
    timefnum_=timefnum
    while (timeinum < timefnum_)
        'set line 'subwrd(cols,ncol)' 1 12'
        timefnum_=timefnum_-30
        if (timefnum_ < timeinum)
            timefnum_=timeinum
        endif
        'set t 'timefnum_
        'q time'
        dateinfo=subwrd(result,3)
        daten=substr(dateinfo,4,9)
        'q w2xy 'daten' 'y0
        xi=subwrd(result,3); yi=subwrd(result,6)
        'drawpoly 'xi' 'yf' 'xf' 'yf
        xf=xi; yf=yi; ncol=ncol+1
    endwhile

    status=0
    'set line 1 1 5'
    while (status != 2)
        marks = read(''profout'/'profcode'-traj2.txt')
        status = subwrd(marks,1)
        if (status=2)
            break
        endif
        datepoint=subwrd(marks,6)
        'q w2xy 'datepoint' 500'
        xi=subwrd(result,3); yi=subwrd(result,6)
        'draw mark 4 'xi' 'yi' 0.05'
    endwhile

*********************************
    'set time 'datei' 'datef
    'define tsuav = ave(temp_anom.3,t-5,t+5)'
    'tsuav = ave(tsuav,t-5,t+5)'
    'define temp = ave(temperature.3,t-5,t+5)'
    'temp = ave(temp,t-5,t+5)'

    'subplot 3 2 5 'opt
    'set gxout shaded'
    'set yflip on'
    'set clevs 'clev
    'set ccols 'ccols
    'd tsuav'

    'set gxout contour'
    'set clevs 'clev
    'set cthick 1'
    'd tsuav'

    'set ccolor 1'
    'set clevs 'iso
    'set cthick 6'
    'set clab masked'
    'd temp'

    'cbarn 0.6 0 2.9 0.4'

    t0=datef
    y0=500
    'q w2xy 't0' 'y0
    xf=subwrd(result,3); yf=subwrd(result,6)

    ncol=1
    timefnum_=timefnum
    while (timeinum < timefnum_)
        'set line 'subwrd(cols,ncol)' 1 12'
        timefnum_=timefnum_-30
        if (timefnum_ < timeinum)
            timefnum_=timeinum
        endif
        'set t 'timefnum_
        'q time'
        dateinfo=subwrd(result,3)
        daten=substr(dateinfo,4,9)
        'q w2xy 'daten' 'y0
        xi=subwrd(result,3); yi=subwrd(result,6)
        'drawpoly 'xi' 'yf' 'xf' 'yf
        xf=xi; yf=yi; ncol=ncol+1
    endwhile

    status=0
    'set line 1 1 5'
    while (status != 2)
        marks = read(''profout'/'profcode'-traj3.txt')
        status = subwrd(marks,1)
        if (status=2)
            break
        endif
        datepoint=subwrd(marks,6)
        'q w2xy 'datepoint' 500'
        xi=subwrd(result,3); yi=subwrd(result,6)
        'draw mark 4 'xi' 'yi' 0.05'
    endwhile

*********************************
    'set dfile 4'
    'subplot 1 2 2 'opt
    'set mpdset hires'
    'set t last'
    'set lat 'maplat1' 'maplat2
    'set lev 0'
    'set lon 'maplon1' 'maplon2
    'set map 0 1 0'
    'set clevs 0'
    'set ylint 1'
    'set xlint 1'
    'set ccols 0 0'
    'd pottmp.4'

    'set rgb 40 190 190 190 -70'
    'set shpopts 40'
    'set line 40 1 0'
    'draw shp /data/users/grivera/Shapes/costa_200mn_mask.shp'

    'set rgb 41 180 180 180 -70'
    'set shpopts 41'
    'set line 41 1 0'
    'draw shp /data/users/grivera/Shapes/costa_100mn_mask.shp'

    'set rgb 42 170 170 170 -70'
    'set shpopts 42'
    'set line 42 1 0'
    'draw shp /data/users/grivera/Shapes/costa_50mn_mask.shp'

    'set shpopts 0'
    'set line 1 1 4'
    'draw shp /data/users/grivera/Shapes/southamerica/po_Sudamerica_GEO_v20.shp'

    'set clevs 0'
    'd pottmp.4'

    'set line 40 1 0'
    'draw mark 5 6.05 2.3 0.2'
    'draw mark 5 6.05 2.05 0.2'
    'draw mark 5 6.05 1.8 0.2'

    'set line 41 1 0'
    'draw mark 5 6.05 2.05 0.2'
    'draw mark 5 6.05 1.8 0.2'

    'set line 42 1 0'
    'draw mark 5 6.05 1.8 0.2'

    'set strsiz 0.1 0.15'
    'set string 1 l 5'
    'draw string 6.2 2.3 100-200nm'
    'draw string 6.2 2.05 50-100nm'
    'draw string 6.2 1.8 0-50nm'

    status=0
    plat=0
    plon=0
    ncol=1
    n=0
    col = 9
    while (status != 2)
        marks = read(''profout'/'profcode'-traj4.txt')
        status = subwrd(marks,1)
        if (status=2)
            break
        endif
        lat = subwrd(marks,3)
        lon = subwrd(marks,4)
        class = subwrd(marks,5)
        if (n=0)
            pclass=class
            if (pclass=11)
                ncol=2
            endif
        endif
        if (class!=pclass)
            ncol = ncol +1
            col=subwrd(colstraj,ncol)
            pclass=class
        endif
        if (plat!=0)
            'set line 'col' 1 10'
            'drawpoly opened -by world 'plon' 'plat' 'lon' 'lat
        endif
        plat=lat
        plon=lon
        n=n+1
    endwhile


    'set strsiz 0.15 0.2'
    'set string 1 c 5'
    'draw string 8.5 7.85 ARGO Profiler #'profcode''

    'set strsiz 0.093 0.1'
    'set string 1 c 3'
    'draw string 8.5 7.59 'datei'-'datef


    'set strsiz 0.093 0.1'
    'set string 1 l 6'
    'draw string 0.55 7.9 a)'
    'draw string 0.55 5.4 b)'
    'draw string 0.55 2.9 c)'
    'draw string 5.95 7.2 d)'


    'set strsiz 0.093 0.1'
    'set string 1 l 3'
    'draw string 5.8 1 Source: ARGO GDAC   Processing: IGP   Latest data: 'datef
    'draw string 5.8 0.75 Clim: 1981-2010 - a)GODAS, b)SODA, c)IMARPE'
    'draw string 5.8 0.5 11-day running mean x2'


    st=0
    k=0
    while (st != 2)
        mark = read(''profout'/'profcode'-traj5.txt')
        st = subwrd(mark,1)
        if (st=2)
            break
        endif
        lat = subwrd(mark,3)
        lon = subwrd(mark,4)
        'set line 1 1 4'
        if (k=0)
            'q w2xy 'lon' 'lat
            xi=subwrd(result,3); yi=subwrd(result,6)
            'draw mark 3 'xi' 'yi' 0.12'
        else
            'q w2xy 'lon' 'lat
            xi=subwrd(result,3); yi=subwrd(result,6)
            'draw mark 3 'xi' 'yi' 0.06'
        endif
        k=k+1
    endwhile

    'set line 1 1 4'
    'q w2xy 'lon' 'lat
    xi=subwrd(result,3); yi=subwrd(result,6)
    'draw mark 2 'xi' 'yi' 0.12'


************
    'gxprint 'outdir''name''iso'_'datef'.eps'
    'gxprint 'outdir''name''iso'_latest.eps'

'quit'


