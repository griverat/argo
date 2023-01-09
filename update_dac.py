import argparse

import argopy
from argopy import IndexFetcher as ArgoIndexFetcher
from dmelon.ocean.argo import build_dl, launch_shell

ARGO_localFTP = "/data/datos/ARGO/gdac"


def main(kind, args):
    argopy.set_options(src="gdac", ftp=ARGO_localFTP)
    argopy.set_options(mode="expert")
    index_loader = ArgoIndexFetcher()
    if kind == "region":
        region = [
            float(args[0]),
            float(args[1]),
            float(args[2]),
            float(args[3]),
            *args[4:],
        ]
        print(region)
        argo_df = index_loader.region(region).to_dataframe()
    elif kind == "floats":
        argo_df = index_loader.float(args).to_dataframe()
    dl_list = build_dl(argo_df, ARGO_localFTP)
    new_dl_list = []
    for num, cmd in enumerate(dl_list):
        if (num + 1) % 20 == 0:
            new_dl_list.append("echo 'Sleeping 60s' ; sleep 60")
        new_dl_list.append(cmd)
    print("Download commands built, launching subshell")
    launch_shell(new_dl_list)
    print("Done")


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description="Selectively update the ARGO local FTP dac database"
    )
    parser.add_argument(
        "kind", type=str, help="region or floats", choices=["region", "floats"]
    )
    parser.add_argument("-l", "--list", nargs="+", help="other args", required=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = getArgs()
    main(args.kind, args.list)
