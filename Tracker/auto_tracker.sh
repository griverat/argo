#!/bin/bash
#Created on Sun Aug 11 06:16:14 2019
#Author: Gerardo A. Rivera Tello
#Email: gerardo_art@me.com
#-----

python argo_tracker.py 10 'patch' \
    --reg_list='-2,2;252.5,259' \
    --reg_list='-2,2;262.5,268.5' \
    --reg_list='-10,0;270,280' \
    --plat -15 5 --plon 250 285

python argo_tracker.py 10 'peru' \
    --reg_list='-20,0;270,290' \
    --plat -25 5 --plon 260 295

python argo_tracker.py 10 'eqstrat' \
    --reg_list='-1.5,2;252.5,259' \
    --reg_list='-22,-16;272.5,280' \
    --plat -25 5 --plon 250 285