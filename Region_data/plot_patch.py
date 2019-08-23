#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Fri Aug 23 04:50:45 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

import os
import json

if __name__ == "__main__":
    with open("./../paths.json") as f:
        paths = json.load(f)
    os.chdir(os.path.join(paths["ARGO_REG_DIR"], "plot_scripts"))
    os.system("grads -blc 'run argo_zones.gs {}'".format(paths["ARGO_PATCH_OUT"]))
