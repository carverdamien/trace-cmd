def sched_rq_size_change(df):
    import numpy as np
    df = df['sched_rq_size_change']
    rq_size = np.array(df['rq_size'])
    timestamp = np.array(df.index, dtype=float)
    cpu = np.array(df['rq_cpu'], dtype=float)
    return {
        'x0' : timestamp,
        'x1' : timestamp,
        'y0' : cpu,
        'y1' : cpu + 0.5,
        'rq_size' : rq_size,
    }
