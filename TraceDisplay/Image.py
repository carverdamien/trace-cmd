from DataFrameCollection import DataFrameCollection, FileExtensionError
import os
import logging
import pandas as pd
import numpy as np

class ShapeCollection(object):
    def __init__(self, dict_of_function={}):
        self.shape = {}
        for v,k in dict_of_function.items():
            self[k] = v
    def __getitem__(self, k):
        return self.shape[k]
    def __setitem__(self, k, v):
        assert hasattr(v, '__call__')
        self.shape[k] = v
    def __iter__(self):
        return iter(self.shape)

def GenerateDefaultShape(k):
    def default_shape(df):
        df = df[k]
        timestamp = np.array(df.index, dtype=float)
        cpu = np.array(df['cpu'], dtype=float)
        data = {
            'x0': timestamp,
            'x1': timestamp,
            'y0' : cpu,
            'y1' : cpu + 0.5,
        }
        columns = filter(lambda k: k not in ['cpu'], df.columns)
        for k in columns:
            data[k] = df[k]
        return data
    return default_shape

def DefaultShapeCollection(trace):
    return ShapeCollection({
        k : GenerateDefaultShape(k)
        for k in trace
    })

class Image(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
    def load(self, path):
        super(Image, self).load(path)
        # TODO: raise exception if DataFrameCollection is not an Image
        for k,v in self.df.items():
            for kk in ['x0','x1','y0','y1']:
                assert kk in v.columns

    def build(self, trace, shapes=None):
        df = {}
        if shapes is None:
            shapes = DefaultShapeCollection(trace)
        # TODO: in parallel
        for name, func in shapes:
            logging.info('Building %s' % name)
            df[name] = pd.DataFrame(func(trace))
        self.df = df

def Shapes_from(shape_path):
    logging.info('Reading %s' % shape_path)
    new_globals = {}
    new_locals = {}
    execfile(shape_path, new_globals, new_locals)
    if 'SHAPES' in new_locals:
        SHAPES = new_locals['SHAPES']
        assert isinstance(SHAPES, dict)
        SHAPES = SHAPES.items()
    else:
        # Every function is a shape rule
        SHAPES = list(filter(
            lambda i : callable(i[1]),
            new_locals.items())
        )
    for k,v in SHAPES:
        assert isinstance(k, str)
        assert callable(v)
    return SHAPES
