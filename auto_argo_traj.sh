#!/bin/bash
#Created on Tue Jan 22 10:09:32 2019
#Author: Gerardo A. Rivera Tello
#Email: grivera@igp.gob.pe
#-----
#Copyright (c) 2018 Instituto Geofisico del Peru
#-----

DIR='/home/grivera/ARGO'
ndates=120
name='prof_list.txt'
cd $DIR || echo Folder not found

source activate Work

python read_argo.py ${ndates} ${name} -0.5 0.5

sh get_traj_argo.sh prof_list.txt

echo Completed
