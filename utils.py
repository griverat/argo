#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Tue Aug 20 11:48:51 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

import os


def check_folder(base_path, name=None):
    if name is not None:
        out_path = os.path.join(base_path, str(name))
    else:
        out_path = base_path
    if not os.path.exists(out_path):
        os.mkdirs(name)
