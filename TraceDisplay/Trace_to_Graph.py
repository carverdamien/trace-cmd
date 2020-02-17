#!/usr/bin/env python2.7
from Graph import Graph
import logging
import os

def Trace_to_Graph(trace_path, pkl_path):
    g = Graph()
    g.load_trace(trace_path)
    g.save(pkl_path)

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Converts a trace-cmd record file into a Graph and save it.",
    )
    parser.add_argument("pkl_path",
                        type=str,
                        help="path to the pickle output file",
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
        if os.path.splitext(args.pkl_path)[1] != '.pkl':
            logging.warn('hfd_path extension should be .pkl')
        if os.path.exists(args.pkl_path):
            logging.error('File %s exists' % args.pkl_path)
            sys.exit(1)
    Trace_to_Graph(args.trace_path,
         args.pkl_path,
    )
