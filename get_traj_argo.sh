#!/bin/bash
#Created on Mon Jan 21 11:11:51 2019
#Author: Gerardo A. Rivera Tello
#Email: grivera@igp.gob.pe
#-----
#Copyright (c) 2018 Instituto Geofisico del Peru
#-----

### DO NOT CHANGE UNLESS THE FTP ADDRESS, DAC
### OR FILE EXTENSION HAS CHANGED
FTP='https://www.usgodae.org/pub/outgoing/argo/dac/'
DAC=(aoml bodc coriolis csio csiro incois jma kma kordi meds nmdis)
TRAJ_ext='_Rtraj.nc'

OUTPUT='/data/users/grivera/ARGO-traj/'

download_data () {
    file_name="${2}""${TRAJ_ext}"
    args="-N -o wget_log --backups=1"
    echo OUTPUT dir set to: "${1}"
    echo filename: "${file_name}"
    cd ${OUTPUT} || echo Change Dir failed
    rm wget_log || echo No previous log file found
    for i in "${DAC[@]}"; do
        echo Trying to download from:
        echo ${FTP}"${i}"/"${2}"/"${file_name}"
        wget $args ${FTP}"${i}"/"${2}"/"${file_name}"
        status=$?
        if [ ${status} = 0 ] ; then
            break
        else
            echo File "${file_name}" not found on any DAC > wget_log
        fi

    done
}

while read -r line || [[ -n "$line" ]]; do
    echo "Profile number: $line"
    download_data "$OUTPUT" "$line"
done < "${1}"
