#!/bin/bash
#Created on Sun Jun 9 06:07:19 2019
#Author: Gerardo A. Rivera Tello
#Email: grivera@igp.gob.pe
#-----
#Copyright (c) 2018 Instituto Geofisico del Peru
#-----

source /home/grivera/miniconda3/etc/profile.d/conda.sh
conda activate Work

OUTDIR=/data/users/grivera
SCR_DIR=/home/grivera/GitLab/argo

cd $SCR_DIR || exit

##############################
#   Build profile database   #
##############################
cd "$SCR_DIR/Profiler_list" || exit

python argo_floatpos.py
python argo_to_json.py

cp Output/* $OUTDIR/ARGO-latlon/

##############################
#    Build Trajectory plot   #
##############################

cd "$SCR_DIR/Trajectory" || exit

sh argo_run_traj.sh

##############################
#   Build multiple profiles  #
##############################

cd "$SCR_DIR/Region_data" || exit

sh argo_region_nc.sh