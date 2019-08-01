#!/bin/bash -l
#Created on Tue Jul 16 03:46:32 2019
#Author: Gerardo A. Rivera Tello
#Email: grivera@igp.gob.pe
#-----
#Copyright (c) 2019 Instituto Geofisico del Peru
#-----

source /home/grivera/miniconda3/etc/profile.d/conda.sh
conda activate Work

python argo_build_profile.py ../Output/peru.txt

screen -dmS argo1 python argo_filter_traj.py 3901231 --lat -8 -1 --lon 275 282
screen -dmS argo2 python argo_filter_traj.py 3901259 --lat -22 -15 --lon 284 291
screen -dmS argo3 python argo_filter_traj.py 3901808 --lat -15 -8 --lon 276 283
screen -dmS argo4 python argo_filter_traj.py 3901185 --lat -19 -12 --lon 278 285
screen -dmS argo5 python argo_filter_traj.py 3901243 --lat -13 -6 --lon 276 283
screen -dmS argo5 python argo_filter_traj.py 3901307 --lat -3.5 3.5 --lon 262 269