#!/usr/bin/env python2.7
import tracecmd
import pandas as pd
import logging

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

def main(trace_path, df_path):
    df = DataFrames_from(trace_path)
    for k in df:
        print(df[k])
    DataFrames_to(df, df_path)

def DataFrames_to(df, df_path):
    # TODO
    pass

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
    import sys
    # trace_path = sys.argv
    logging.basicConfig(level=logging.DEBUG)
    main("trace.dat","trace.pandas")
