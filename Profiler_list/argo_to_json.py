#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Mon Jun 3 04:37:36 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

import pandas as pd
import json

def parse_db(argo_file):
    argo_data = pd.read_csv(argo_file,parse_dates=[0])
    platfs = argo_data['platfn'].unique()
    container = {}
    for platf in platfs:
        db_subset = argo_data.query("platfn==@platf").reset_index(drop=True).sort_values(by=['date'])
        for r in db_subset.itertuples():
            try:
                container[f"{platf}"].update({"{:02d}".format((r.Index)):{'date':"{:%Y-%m-%d}".format(r.date),
                                    'lat':r.lat,'lon':r.lon,'nprof':r.nprof}})
            except:
                container[f"{platf}"]={"{:02d}".format(r.Index):{'date':"{:%Y-%m-%d}".format(r.date),
                                    'lat':r.lat,'lon':r.lon,'nprof':r.nprof}}
    container = json.dumps(container)
    container = json.loads(container)
    return container

if __name__ == "__main__":
    ARGO_DB = "Output/latlontemp.txt"
    data = parse_db(ARGO_DB)
    with open('Output/argodb.json', 'w') as outfile:
        json.dump(data, outfile)
