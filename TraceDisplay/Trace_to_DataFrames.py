#!/usr/bin/env python2.7
from Trace import Trace
import logging
import os

def Trace_to_DataFrames(trace_path, hdf_path):
    t = Trace()
    t.load(trace_path)
    t.save(hdf_path)

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Converts a trace-cmd record file into pandas dataframes and save them.",
    )
    parser.add_argument("hdf_path",
                        type=str,
                        help="path to the pandas dataframes output file",
    )
    parser.add_argument("trace_path",
                        type=str,
                        help="path to the trace-cmd record input file",
    )
    parser.add_argument("--force","-f",
                        action="store_true",
                        help="overwrites output file if it already exists",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(args.trace_path):
        logging.error('Cannot find %s' % args.trace_path)
        sys.exit(1)
    if not args.force:
        if os.path.splitext(args.trace_path)[1] != '.dat':
            logging.warn('trace_path extension should be .dat')
        if os.path.splitext(args.hdf_path)[1] != '.h5':
            logging.warn('hfd_path extension should be .h5')
        if os.path.exists(args.hdf_path):
            logging.error('File %s exists' % args.hdf_path)
            sys.exit(1)
    Trace_to_DataFrames(args.trace_path,
         args.hdf_path,
    )
