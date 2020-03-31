#!/usr/bin/env python2.7
from Trace import Trace
import logging
import os
import pandas as pd
MAX = 999999
pd.options.display.max_rows = MAX
pd.options.display.max_columns = MAX
pd.options.display.max_colwidth = MAX
pd.options.display.width = MAX

def Trace_timeline(trace_path, timestamp, size):
    t = Trace()
    t.load(trace_path)
    print(t.timeline(timestamp, size))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Shows a merged timeline of events.",
    )
    parser.add_argument("trace_path",
                        type=str,
                        help="path to the trace file",
    )
    parser.add_argument("--timestamp", "-t",
                        type=int,
                        help="show events around this timestamp.",
                        default=0,
    )
    parser.add_argument("--size", "-s",
                        type=int,
                        help="show at most size events before (after) the timestamp.",
                        default=10,
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    Trace_timeline(args.trace_path,
                   args.timestamp,
                   args.size,
    )
