from DataFrameCollection import DataFrameCollection, FileExtensionError
import os
import tracecmd
import pandas as pd
import logging

class Trace(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Trace, self).__init__(*args, **kwargs)
    def load(self, path):
        if os.path.splitext(path)[1] == '.h5':
            super(Trace, self).load(path)
            # TODO: raise exception if DataFrameCollection is not a Trace
            for k,v in self.df.items():
                assert v.index.name == 'timestamp'
            return
        elif os.path.splitext(path)[1] != '.dat':
            raise FileExtensionError()
        df = {}
        trace = tracecmd.Trace(path)
        # TODO: in parallel
        for cpu in range(trace.cpus):
            logging.info('Reading events of cpu %d' % cpu)
            event = trace.read_event(cpu)
            while event:
                event = event_to_dict(event)
                # TODO: Maybe del event['event']
                df.setdefault(event['event'],[]).append(event)
                event = trace.read_event(cpu)
        logging.info('%s contains %d types of events' %
                     (path, len(df)))
        # TODO: in parallel
        for event in df:
            logging.info('Building DataFrame of event %s' % event)
            df[event] = pd.DataFrame(df[event])
            # TODO: check if timestamps are unique
            # because two cpu can produce the same timestamp
            df[event].set_index('timestamp', inplace=True)
            df[event].sort_index(inplace=True, ascending=True)
        self.df = df

def try_str_except_int(x):
    try:
        return str(x)
    except UnicodeDecodeError as e:
        return int(x)

CAST = {
    'long' : int,
    'u64' : int,
    'int' : int,
    'unsigned int' : int,
    'pid_t' : int,
    'size_t' : int,
    'const char *' : try_str_except_int,
    'char *' : try_str_except_int,
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
