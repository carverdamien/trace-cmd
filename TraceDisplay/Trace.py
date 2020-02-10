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
    def timeline(self, timestamp=0, size=10):
        assert size > 0
        def select(v):
            i = v.index.searchsorted(timestamp)
            imin = max(0, i - size)
            imax = min(len(v), i + size+1)
            return v.iloc[imin:imax]
        timeline = {
            k : select(v)
            for k,v in self.items()
        }
        timeline = pd.concat([v for k,v in timeline.items()], sort=False)
        timeline.sort_index(inplace=True, ascending=True)
        i = timeline.index.searchsorted(timestamp)
        imin = max(0, i - size)
        imax = min(len(timeline), i + size+1)
        timeline = timeline.iloc[imin:imax]
        timeline = timeline.dropna(how='all', axis=1)
        return timeline

def try_str_except_int(x):
    try:
        return str(x)
    except UnicodeEncodeError as e:
        return int(x)
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

"""
import tracecmd
import ctracecmd as c
let e be any sched_switch event

How do I get the meaning of e['prev_state']? i.e. {S,D,T,t,X,Z,P,I,R}{+,} ?

The trace.dat file has a copy of /sys/kernel/debug/tracing/events/sched/sched_switch/format
but I was not able to to get the 'print fmt' information from the python API.
The answer is in lib/traceevent/event-parse.c (7Kloc), but for now I tried the following:

fmt = c.tep_event_print_fmt_get(e._format)
c.tep_print_fmt_format_get(fmt)
'prev_comm=%s prev_pid=%d prev_prio=%d prev_state=%s%s ==> next_comm=%s next_pid=%d next_prio=%d'
args = c.tep_print_fmt_args_get(fmt)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'prev_comm'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'prev_pid'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'prev_prio'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'?'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'?'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'next_comm'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'next_pid'
args = c.tep_print_arg_next_get(args)
arg_field = c.tep_print_arg_field_get(args)
c.tep_print_arg_field_name_get(arg_field)
'next_prio'
"""

"""
name: sched_switch
ID: 316
format:
        field:unsigned short common_type;       offset:0;       size:2; signed:0;
        field:unsigned char common_flags;       offset:2;       size:1; signed:0;
        field:unsigned char common_preempt_count;       offset:3;       size:1; signed:0;
        field:int common_pid;   offset:4;       size:4; signed:1;

        field:char prev_comm[16];       offset:8;       size:16;        signed:1;
        field:pid_t prev_pid;   offset:24;      size:4; signed:1;
        field:int prev_prio;    offset:28;      size:4; signed:1;
        field:long prev_state;  offset:32;      size:8; signed:1;
        field:char next_comm[16];       offset:40;      size:16;        signed:1;
        field:pid_t next_pid;   offset:56;      size:4; signed:1;
        field:int next_prio;    offset:60;      size:4; signed:1;

print fmt: "prev_comm=%s prev_pid=%d prev_prio=%d prev_state=%s%s ==> next_comm=%s next_pid=%d next_prio=%d", REC->prev_comm, REC->prev_pid, REC->prev_prio, (REC->prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1)) ? __print_flags(REC->prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1), "|", { 0x0001, "S" }, { 0x0002, "D" }, { 0x0004, "T" }, { 0x0008, "t" }, { 0x0010, "X" }, { 0x0020, "Z" }, { 0x0040, "P" }, { 0x0080, "I" }) : "R", REC->prev_state & (((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) ? "+" : "", REC->next_comm, REC->next_pid, REC->next_prio
"""
