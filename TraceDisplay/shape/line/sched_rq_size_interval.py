def sched_rq_size_interval(df):
    import numpy as np
    df = df['sched_rq_size_change']
    timestamp = np.array(df.index, dtype=float)
    next_timestamp_on_same_cpu = np.array(df.index, dtype=float)
    rq_size = np.array(df['rq_size'])
    cpu = np.array(df['rq_cpu'], dtype=float)
    idx = np.arange(len(next_timestamp_on_same_cpu))
    # TODO: in parallel
    for i in np.unique(cpu):
        sel = cpu == i
        next_timestamp_on_same_cpu[idx[sel][:-1]] = next_timestamp_on_same_cpu[idx[sel][1:]]
    return {
        'x0' : timestamp,
        'x1' : next_timestamp_on_same_cpu,
        'y0' : cpu,
        'y1' : cpu,
        'rq_size' : rq_size,
    }
