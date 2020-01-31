def sched_rq_size_interval(df):
    import numpy as np
    df = df['sched_rq_size_change']
    size = np.array(df['size'])
    timestamp = np.array(df.index)
    next_timestamp_on_same_cpu = np.array(df.index)
    cpu = np.array(df['cpu'])
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
        'size' : size,
    }
