from DataFrameCollection import DataFrameCollection, FileExtensionError
import os
import logging
import pandas as pd

class Image(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
    def load(self, path):
        super(Image, self).load(path)
        # TODO: raise exception if DataFrameCollection is not an Image
        for k,v in self.df.items():
            for kk in ['x0','x1','y0','y1']:
                assert kk in v.columns

    def build(self, trace, shapes):
        df = {}
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
