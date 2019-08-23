function main(args)
    'reinit'
    say args
    if ( args='?' )
        say 'This script needs 1 argument: patchdir'
        return
    else
        patchdir=subwrd(args,1)
    endif

    say "patchdir set to: "patchdir

    compute=1
    'c'
    if (compute = 1)
        'reinit'
        'set display color white'
        'c'
        'set grads off'
        'rgbset2'

        outdir='../Output/'
        name='argo_anom_zones'

**********
        'sdfopen 'patchdir'/argo_tanom_252.5,259.0_-1.5,2.5.nc'
        'sdfopen 'patchdir'/argo_temp_252.5,259.0_-1.5,2.5.nc'

        'sdfopen 'patchdir'/argo_tanom_272.5,280.0_-22.0,-16.0.nc'
        'sdfopen 'patchdir'/argo_temp_272.5,280.0_-22.0,-16.0.nc'
**********

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

        'set lev 0 500'
        'set time 'datei' 'datef
        'set x 1'
        'set y 1'
        'define tsuav1 = ave(tanom.1,t-5,t+5)'

        'set dfile 3'
        'set lev 0 500'
        'set time 'datei' 'datef
        'set x 1'
        'set y 1'
        'define tsuav2 = ave(tanom.3,t-5,t+5)'
    endif
**********
    'set dfile 3'
    'set lev 0 500'
    'set time 'datei' 'datef
    'set x 1'
    'set y 1'
    opt='0.5 1.5 1 1.5 1'
    clev='-6 -5 -4 -3 -2 -1 -0.5 0.5 1  2  3  4  5  6'
    ccols='49 48  47 46 44 42 41   0  21 22 24 26 27 28 29'

************
    'set parea 0.6 10.4 5.3 8'
    'set clevs 'clev
    'set ccols 'ccols
    'set yflip on'
    'set xlopts 0 0 0'
    'set gxout grfill'
    'd tsuav1'

    'set gxout contour'
    'set clevs 'clev
    'set ccolor 1'
    'set cthick 1'
    'd tsuav1'


************
    'set parea 0.6 10.4 1.3 4'
    'set clevs 'clev
    'set ccols 'ccols
    'set yflip on'
    'set gxout grfill'
    'd tsuav2'

    'set gxout contour'
    'set clevs 'clev
    'set ccolor 1'
    'set cthick 1'
    'd tsuav2'

    'set strsiz 0.13 0.14'
    'set string 1 c 4'
    'draw string 5.5 8.2 a) Zone 1 [107.5`3.`0W-101.0`3.`0W] [1.5`3.`0S-2.5`3.`0N]'
    'draw string 5.5 4.2 b) Zone 2 [87.5`3.`0W-80.0`3.`0W] [22.0`3.`0S-16.0`3.`0S]'
    'set strsiz 0.09 0.1'
    'draw string 9.55 4.1 11-day running mean'
    'draw string 9.55 8.1 11-day running mean'

    'set strsiz 0.08 0.1'
    'set string 1 c 4'

*************************

    'set dfile 1'
    'set parea 0.6 10.4 4.7 5.3'
    'set x 1'
    'set y 1'
    'set z 1'
    'set xlopts 1 3 0.11'
    'set yflip off'
    'set ylpos 0 r'
    'set ylopts 0 0 0'
    'set gxout bar'
    'set bargap 0'
    'set barbase 0'
    'set vrange 0 6';'set ylint 1'
    'set ccolor 1'
    'd prof_count.1'

    'set ylopts 1 3 0.1'
    'set ylint 2'
    'd prof_count.1*0'


    'set dfile 3'
    'set parea 0.6 10.4 0.7 1.3'
    'set x 1'
    'set y 1'
    'set z 1'
    'set yflip off'
    'set ylpos 0 r'
    'set ylopts 0 0 0'
    'set gxout bar'
    'set bargap 0'
    'set barbase 0'
    'set vrange 0 6';'set ylint 1'
    'set ccolor 1'
    'd prof_count.3'

    'set ylopts 1 3 0.1'
    'set ylint 2'
    'd prof_count.3*0'


*'cbarn'
************
    'gxprint 'outdir''name'.eps'
    'gxprint 'outdir''name'.png'

'quit'


