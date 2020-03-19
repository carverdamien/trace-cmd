from DataFrameCollection import DataFrameCollection, FileExtensionError
import os
import logging
import pandas as pd
import numpy as np

class Category(object):
    def __init__(self, color, label):
        super(Category, self).__init__()
        self.color = color
        self.label = label

class Shape(object):
    """AbstractShape"""
    shape_name = 'Shape'
    shape_fields = ['category']
    def __call__(self, *args, **kwargs):
        logging.error('AbstractShape should not be called.')
        return {
            'category' : [],
        }

class LineShape(Shape):
    """AbstractShape"""
    shape_name = 'LineShape'
    shape_fields = Shape.shape_fields + ['x0','x1','y0','y1']
    def __call__(self, *args, **kwargs):
        logging.error('AbstractShape should not be called.')
        return {
            'category' : [],
            'x0'       : [],
            'x1'       : [],
            'y0'       : [],
            'y1'       : [],
        }

class DefaultLineShape(LineShape):
    def __init__(self, key, *args, **kwargs):
        super(DefaultLineShape, self).__init__(*args, **kwargs)
        self.key = key
    def __call__(self, *args, **kwargs):
        df, = args
        df = df[self.key]
        timestamp = np.array(df.index, dtype=float)
        cpu = np.array(df['cpu'], dtype=float)
        data = {
            'x0'       : timestamp,
            'x1'       : timestamp,
            'y0'       : cpu,
            'y1'       : cpu + 0.5,
            'category' : np.zeros(len(timestamp), dtype=int),
        }
        columns = filter(lambda k: k not in ['cpu'], df.columns)
        for k in columns:
            assert k not in self.__class__.shape_fields
            data[k] = df[k]
        return data

class ShapeCollection(object):
    def __init__(self, shape={}):
        self.shape = {}
        for k,v in shape.items():
            self[k] = v
    def __getitem__(self, k):
        return self.shape[k]
    def __setitem__(self, k, v):
        assert isinstance(v, Shape)
        self.shape[k] = v
    def __iter__(self):
        return iter(self.shape)
    def items(self):
        return self.shape.items()

def DefaultShapeCollection(trace):
    return ShapeCollection({
        k : DefaultLineShape(k)
        for k in trace
    })

class Image(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.category = [Category(color='#000000',label='default')]
        self.shapes = None

    def load(self, path):
        super(Image, self).load(path)
        # TODO: raise exception if DataFrameCollection is not an Image
        for k,v in self.df.items():
            for kk in LineShape.shape_fields:
                assert kk in v.columns
        # For now, the only shape available is line.
        # Assume we are loading lines.
        # TODO: we need to save the type of the shape
        self.shapes = ShapeCollection({
            k : LineShape()
            for k in self.df
        })

    def build(self, trace, shapes=None):
        df = {}
        if shapes is None:
            shapes = DefaultShapeCollection(trace)
        assert isinstance(shapes, ShapeCollection)
        # TODO: in parallel
        for name, func in shapes.items():
            logging.info('Building %s' % name)
            df[name] = pd.DataFrame(func(trace))
        self.shapes = shapes
        self.df = df

    def line(self):
        def df(k):
            shape_fields = self.shapes[k].__class__.shape_fields
            todrop = list(filter(lambda k : k not in shape_fields, self.df[k].columns))
            return self.df[k].drop(columns=todrop)
        line = pd.concat([df(k) for k in filter(lambda k: isinstance(k, LineShape), self.shapes)])
        line['category'] = line['category'].astype('category')
        color_key = [self.category[category].color for category in np.unique(line['category'])]
        return line, color_key
