def test_random_lines(df):
    import numpy as np
    N = max(100, sum([len(v) for k,v in df.items()]))
    return {
        'x0' : np.random.random(N),
        'x1' : np.random.random(N),
        'y0' : np.random.random(N),
        'y1' : np.random.random(N),
        'tag' : np.random.random(N),
    }
