#!/usr/bin/env python2.7
import tracecmd
import pandas as pd
import logging
import os

CAST = {
    'long' : int,
    'u64' : int,
    'int' : int,
    'pid_t' : int,
    'char[16]' : str,
    '__data_loc char[]' : str,
}

def typeof(key, event):
    return tracecmd.tep_format_field_type_get(event[str(key)]._field)

def event_to_dict(event):
    ret = {
        'event'        : event.name,
        'timestamp'    : event.ts,
        'cpu'          : event.cpu,
        'common_comm'  : event.comm,
    }
    ret.update({
        common:event.num_field(common)
        for common in [
                # "common_type", # TODO: store this instead of name?
                "common_flags",
                "common_preempt_count",
                "common_pid",
        ]
    })
    ret.update({
        key:CAST[typeof(key,event)](event[str(key)])
        for key in event.keys()
    })
    return ret

def main(trace_path, hdf_path):
    df = DataFrames_from(trace_path)
    DataFrames_to_hdf(df, hdf_path)

def DataFrames_to_hdf(df, hdf_path):
    if os.path.exists(hdf_path):
        logging.info('Overwriting %s' % hdf_path)
        os.remove(hdf_path)
    for k in df:
        logging.info('Saving %s' % k)
        df[k].to_hdf(hdf_path, key=k, mode='a')

def DataFrames_from(trace_path):
    df = {
        # event : pd.DataFrame()
    }
    datadict = DataDict_from(trace_path)
    logging.info('%s contains %d types of events' % (
        trace_path, len(datadict)))
    # TODO: in parallel
    for event in datadict:
        logging.info('Building DataFrame of event %s' % event)
        df[event] = pd.DataFrame(datadict[event])
        df[event].set_index('timestamp', inplace=True)
        df[event].sort_index(inplace=True, ascending=True)
    return df

def DataDict_from(trace_path):
    datadict = {
        # name : [e where e.event==name]
    }
    trace = tracecmd.Trace(trace_path)
    # TODO: in parallel
    for cpu in range(trace.cpus):
        logging.info('Reading events of cpu %d' % cpu)
        event = trace.read_event(cpu)
        while event:
            event = event_to_dict(event)
            datadict.setdefault(event['event'],[]).append(event)
            event = trace.read_event(cpu)
    return datadict

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
    main(args.trace_path,
         args.hdf_path,
    )
