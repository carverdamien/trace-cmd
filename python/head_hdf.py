#!/usr/bin/env python2.7
import pandas as pd
import os

def main(hdf_path):
    with pd.HDFStore(hdf_path) as store:
        for k in store.keys():
            print(k)
            print(store[k].head())
    pass

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Show first lines of each dataframes",
    )
    parser.add_argument("hdf_path",
                        type=str,
                        help="path to hdf file",
    )
    args = parser.parse_args()
    if not os.path.exists(args.hdf_path):
        print('Cannot find %s' % hdf_path)
        sys.exit(1)
    main(args.hdf_path)
