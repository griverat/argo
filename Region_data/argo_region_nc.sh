#!/bin/bash -l
#SBATCH --partition mpi_short2
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 4
#SBATCH --time 04:00:00
#SBATCH --job-name ARGO_region_nc
#SBATCH --output logs/argo_region_nc-%J.txt

conda activate Work

# python argo_region_nc.py -9.5 -6.5 263.5 266.5 1999-01-01 2019-12-31
# python argo_region_nc.py -6.5 -3.5 263.5 266.5 1999-01-01 2019-12-31
##python argo_region_nc.py -2 2 252.5 259 1999-01-01 2019-12-31
# python argo_region_nc.py -2 2 263.5 268.5 1999-01-01 2019-12-31 
##python argo_region_nc.py -2 2 262.5 268.5 1999-01-01 2019-12-31
# python argo_region_nc.py -2 2 270 277 1999-01-01 2019-12-31 
# python argo_region_nc.py -5 0 270 280 1999-01-01 2019-12-31 
##python argo_region_nc.py -10 0 270 280 1999-01-01 2019-12-31
# python argo_region_nc.py -7 -3 275 280 1999-01-01 2019-12-31 
# python argo_region_nc.py -7.5 -4 258 262.5 1999-01-01 2019-12-31 
# python argo_region_nc.py 5.5 10 261.5 267.5 1999-01-01 2019-12-31
python argo_region_nc.py -1.5 2.5 252.5 259 1999-01-01 2019-12-31
python argo_region_nc.py -22 -16 272.5 280 1999-01-01 2019-12-31
