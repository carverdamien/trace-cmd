#!/usr/bin/env python2.7
from Graph import Graph
import logging
import os

def Upload_Graph(input_path, uri):
    g = Graph()
    if os.path.splitext(input_path)[1] == '.dat':
        g.load_trace(input_path)
    elif os.path.splitext(input_path)[1] == '.pkl':
        g.load(input_path)
    g.upload(uri, delete_all=True)

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Upload a TraceGraph in a neo4j GraphDatabase.",
    )
    parser.add_argument("input_path",
                        type=str,
                        help="path to the pickle input file (or path to trace.dat)",
    )
    parser.add_argument("uri",
                        type=str,
                        help="neo4j uri",
    )
    parser.add_argument("--force","-f",
                        action="store_true",
                        help="ignore warnings",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(args.input_path):
        logging.error('Cannot find %s' % args.input_path)
        sys.exit(1)
    if not args.force:
        if os.path.splitext(args.input_path)[1] != '.pkl':
            logging.warn('trace_path extension should be .pkl')
        logging.warn('This operation will erase the current database store on %s' % args.uri)
        logging.info('Press enter to continue')
        sys.stdin.read(1)
    Upload_Graph(args.input_path,
         args.uri,
    )
