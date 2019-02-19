#!/bin/bash
#SBATCH --partition mpi_short2
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 12
#SBATCH --time 00:30:00
#SBATCH --mem-per-cpu 4000
#SBATCH --job-name argo_floatpos
#SBATCH --output logs/argo_floatpos-%J.txt

source /home/grivera/miniconda3/etc/profile.d/conda.sh

conda activate Work

python argo_floatpos.py