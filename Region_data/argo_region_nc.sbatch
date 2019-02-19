#!/bin/bash
#SBATCH --partition mpi_short2
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 12
#SBATCH --time 00:30:00
#SBATCH --job-name ARGO_region_nc
#SBATCH --output logs/argo_region_nc-%J.txt

source /home/grivera/miniconda3/etc/profile.d/conda.sh

conda activate Work

python argo_region_nc.py