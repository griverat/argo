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

import json
import os

import pandas as pd


def parse_db(argo_file):
    argo_data = pd.read_csv(argo_file, parse_dates=[0]).reset_index(drop=True)
    platfs = argo_data["platfn"].unique()
    container = {}
    for platf in platfs:
        db_subset = (
            argo_data.query("platfn==@platf")
            .sort_values(by=["date"])
            .reset_index(drop=True)
        )
        for r in db_subset.itertuples():
            try:
                container[f"{platf}"].update(
                    {
                        "{:02d}".format((r.Index)): {
                            "date": "{:%Y-%m-%d}".format(r.date),
                            "lat": r.lat,
                            "lon": r.lon,
                            "nprof": r.nprof,
                            "depth": r.depth,
                            "bio": r.bio,
                        }
                    }
                )
            except:
                container[f"{platf}"] = {
                    "{:02d}".format(r.Index): {
                        "date": "{:%Y-%m-%d}".format(r.date),
                        "lat": r.lat,
                        "lon": r.lon,
                        "nprof": r.nprof,
                        "depth": r.depth,
                        "bio": r.bio,
                    }
                }
    container = json.dumps(container)
    container = json.loads(container)
    return container


def to_nedb_obj(argo_file):
    argo_data = pd.read_csv(argo_file, parse_dates=[0]).reset_index(drop=True)
    return argo_data.to_json(orient="records")


if __name__ == "__main__":
    with open("./../paths.json") as f:
        paths = json.load(f)
    data = to_nedb_obj(paths["ARGO_DB"])
    with open(os.path.join(paths["ARGO_DB_OUT"], "argodb.json"), "w") as outfile:
        outfile.write(data)
        # json.dump(data, outfile)
