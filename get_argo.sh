#!/bin/bash -l
#Created on Fri Oct 4 14:24:10 2019
#Author: Gerardo A. Rivera Tello
#Email: grivera@igp.gob.pe
#-----
#Copyright (c) 2018 Instituto Geofisico del Peru
#-----

output="/data/datos/ARGO/data/"

for i in {5..0}
do
    year=$(date +%Y -d "-$i day")
    month=$(date +%m -d "-$i day")
    fecha=$(date +%Y%m%d -d "-$i day")
    archivo='_prof.nc'
    fecha2=$fecha$archivo
    # #====================================
    echo $fecha
    
    echo "Descargando el archivo, $fecha$archivo"

    cd ${output}
    rm ${fecha2}

    wget -c  ftp://ftp.ifremer.fr/ifremer/argo/geo/pacific_ocean/$year/$month/$fecha$archivo
    
    if [ -f "${fecha2}"  ]
    then
        echo "El archivo ya fue descargado"
    else
	wget -c ftp://usgodae.org/pub/outgoing/argo/geo/pacific_ocean/$year/$month/$fecha$archivo
    fi
    
    
done
