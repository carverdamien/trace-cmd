from .DataFrameCollection import DataFrameCollection, FileExtensionError
from .parallel import parallel_thread, parallel_process
import os
import pandas as pd
import numpy as np
import logging
import itertools
import gzip, shutil

def nxts_X(df, X):
    next_timestamp = np.array(df.index)
    idx = np.arange(len(next_timestamp))
    X_values = np.array(df[X])
    X_unique = np.unique(X_values)
    @parallel_thread(itertools.product(X_unique))
    def foreach(x):
        sel = X_values == x
        next_timestamp[idx[sel][:-1]] = next_timestamp[idx[sel][1:]]
    df[f'nxts_{X}'] = next_timestamp
    return df

NXTS_X = {
    'sched_rq_size_change' : ['rq_cpu'],
    'sched_switch' : ['cpu'],
}

class Trace(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Trace, self).__init__(*args, **kwargs)
    def load(self, path):
        if os.path.splitext(path)[1] == '.gz':
            new_path = os.path.splitext(path)[0]
            with gzip.open(path, 'rb') as f_in:
                with open(new_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            path = new_path
        if os.path.splitext(path)[1] == '.h5':
            super(Trace, self).load(path)
            # TODO: raise exception
            # if DataFrameCollection is not a Trace
            for k,v in self.items():
                assert v.index.name == 'timestamp'
            return
        elif os.path.splitext(path)[1] != '.dat':
            raise FileExtensionError(path, '.dat')
        #
        ### Read path ###
        #
        # TODO: improve load distribution.
        #       in parallel, per_offset
        #       use trace.read_event_at(offset).
        #
        @parallel_process(itertools.product(range(nr_cpu(path))))
        def foreach(i):
            return i, read_event_of_cpu(path, i)
        cpu = {
            ctx.value[0] : ctx.value[1]
            for ctx in foreach()
        }
        #
        ### Prepare concatenation ###
        #
        event_name = []
        for i in cpu:
            for e in cpu[i]:
                if e in event_name:
                    continue
                event_name.append(e)
        logging.info('%s contains %d types of events' %
                     (path, len(event_name)))
        #
        ### Concatenate ###
        #
        event = {}
        for e in event_name:
            logging.info('Building DataFrame of event %s' % e)
            # Concatenate
            # same event across
            # all cpus
            df = pd.concat([
                pd.DataFrame(cpu[i][e])
                for i in cpu
                if e in cpu[i]
            ])
            # set_index must fail if
            # timestamps are not unique
            # TODO: add unittest
            # TODO: use multi-index if
            # many timestamps are not unique
            df.set_index(
                'timestamp',
                verify_integrity=True,
                inplace=True,
            )
            df.sort_index(
                ascending=True,
                inplace=True,
            )
            event[e] = df
        #
        ### Compute NXTS_X ###
        #
        for k,v in event.items():
            if k in NXTS_X:
                for X in NXTS_X[k]:
                    v = nxts_X(v, X)
            self[k] = v
        print_warning(self, path)
    def timeline(self, timestamp=0, size=10, tmin=None, tmax=None):
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
        if tmin:
            timeline = timeline[timeline.index > tmin]
        if tmax:
            timeline = timeline[timeline.index < tmax]
        timeline = timeline.dropna(how='all', axis=1)
        return timeline

def nr_cpu(trace_path):
    import tracecmd
    # Lazy import (only Linux)
    return tracecmd.Trace(trace_path).cpus

def read_event_of_cpu(trace_path, cpu):
    import tracecmd
    # Lazy import (only Linux)
    event = {}
    trace = tracecmd.Trace(trace_path)
    logging.info('Reading events of cpu %d' % cpu)
    e = trace.read_event(cpu)
    while e:
        e = event_to_dict(e)
        # TODO: Maybe del e['event']
        event.setdefault(e['event'],[]).append(e)
        e = trace.read_event(cpu)
    return event

def try_str_except_int(x):
    try:
        return str(x)
    except UnicodeEncodeError as e:
        return int(x)
    except UnicodeDecodeError as e:
        return int(x)

CAST = {
    # int
    'unsigned long' : int,
    's64' : int,
    'long' : int,
    'u32' : int,
    'u64' : int,
    'int' : int,
    'unsigned' : int,
    'unsigned int' : int,
    'pid_t' : int,
    'size_t' : int,
    'gfp_t' : int,
    'bool' : int,
    'clockid_t' : int,
    'umode_t' : int,
    'enum hrtimer_mode' : int,
    'dev_t' : int,
    'ino_t' : int,
    'ext4_lblk_t' : int,
    'char' : int,
    'short' : int,

    'struct fpu *' : int,
    'const void *' : int,
    'struct page *' : int,
    'u32 *' : int,
    'struct stat *' : int,
    'const char * const *' : int,
    'void *' : int,

    # str except int
    'const char *' : try_str_except_int,
    'char *' : try_str_except_int,

    # str
    'char[16]' : str,
    'char[32]' : str,
    '__data_loc char[]' : str,

    # data
    'unsigned long[6]' : lambda x : str(x.data[:]),
}

def DEFAULT_CAST(t):
    if t not in CAST:
        logging.warn("'%s' not in CAST" % (t))
    return int

def typeof(key, event):
    import tracecmd
    return str(tracecmd.tep_format_field_type_get(event[str(key)]._field))

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
        key:CAST.get(typeof(key,event), DEFAULT_CAST(typeof(key,event)))(event[str(key)])
        for key in event.keys()
    })
    if ret['event'] in EXTRA:
        ret = EXTRA[ret['event']](ret)
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

# TODO: do not use this function, use functions of ctracecmd
def print_prev_state(prev_state):
    def __print_flags(flag, delim, flag_array):
        return delim.join([f[1] for f in filter(lambda f: f[0] & flag, flag_array)])
    if prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1):
        flag = prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1)
        delim = "|"
        flag_array = [
            ( 0x0001, "S" ),
            ( 0x0002, "D" ),
            ( 0x0004, "T" ),
            ( 0x0008, "t" ),
            ( 0x0010, "X" ),
            ( 0x0020, "Z" ),
            ( 0x0040, "P" ),
            ( 0x0080, "I" ),
        ]
        r = __print_flags(flag, delim, flag_array)
    else:
        r = "R"
    if prev_state & (((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1):
        r += "+"
    else:
        r += ""
    return r

def extra_sched_switch(e):
    if 'prev_state' in e:
        e['prev_state'] = print_prev_state(e['prev_state'])
    return e

EXTRA = {
    'sched_switch' : extra_sched_switch,
}

def print_warning(trace, path):
    if 'sched_switch' not in trace:
        return
    import subprocess
    pat = """print fmt: "prev_comm=%s prev_pid=%d prev_prio=%d prev_state=%s%s ==> next_comm=%s next_pid=%d next_prio=%d", REC->prev_comm, REC->prev_pid, REC->prev_prio, (REC->prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1)) ? __print_flags(REC->prev_state & ((((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) - 1), "|", { 0x0001, "S" }, { 0x0002, "D" }, { 0x0004, "T" }, { 0x0008, "t" }, { 0x0010, "X" }, { 0x0020, "Z" }, { 0x0040, "P" }, { 0x0080, "I" }) : "R", REC->prev_state & (((0x0000 | 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040) + 1) << 1) ? "+" : "", REC->next_comm, REC->next_pid, REC->next_prio"""
    returned_value = subprocess.call(['sh','-c',"grep -aF '%s' '%s' | head -n 1 | grep -q '%s'" % (pat, path, pat)])
    if returned_value == 0:
        return
    logging.warn("Could not find '%s' in '%s': sched_switch prev_state might be incorrect." % (pat,pat))
