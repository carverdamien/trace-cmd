def sched_rq_size_change(df):
    import numpy as np
    df = df['/sched_rq_size_change']
    size = np.array(df['size'])
    timestamp = np.array(df.index)
    cpu = np.array(df['cpu'])
    return {
        'x0' : timestamp,
        'x1' : timestamp,
        'y0' : cpu,
        'y1' : cpu + 0.5,
        'size' : size,
    }
