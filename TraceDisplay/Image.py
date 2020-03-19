from DataFrameCollection import DataFrameCollection, FileExtensionError
import os
import logging
import pandas as pd
import numpy as np
import itertools

class Shape(object):
    """AbstractShape"""
    shape_class = 'Shape'
    shape_fields = ['category']
    def __call__(self, *args, **kwargs):
        logging.error('AbstractShape should not be called.')
        return {
            'category' : [],
        }

class PointShape(Shape):
    """AbstractShape"""
    shape_class = 'PointShape'
    shape_fields = Shape.shape_fields + ['x','y']
    def __call__(self, *args, **kwargs):
        logging.error('AbstractShape should not be called.')
        return {
            'category' : [],
            'x'        : [],
            'y'        : [],
        }

class LineShape(Shape):
    """AbstractShape"""
    shape_class = 'LineShape'
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
    def to_DataFrame(self):
        data = []
        index = []
        columns = ['shape_class']
        for k,v in self.items():
            index.append(k)
            data.append([v.shape_class])
        return pd.DataFrame(data, index=index, columns=columns)

def DefaultShapeCollection(trace):
    return ShapeCollection({
        k : DefaultLineShape(k)
        for k in trace
    })

class DefaultCategory(object):
    DEFAULT_COLOR_VALUE = [
        '#660066',
        '#006633',
        '#FFCC00',
        '#CC3333',
        '#996633',
        '#000099',
        '#000000',
        '#0099CC',
        '#868F98',
        '#009999',
        '#CC9999',
        '#66CCCC',
        '#66CC00',
        '#FF6600',
    ]
    def __init__(self):
        self.color = itertools.cycle(self.__class__.DEFAULT_COLOR_VALUE)
    def __call__(self, image):
        data = []
        index = []
        columns = ['color', 'label']
        category = 0
        for k,v in image.items():
            index.append(category)
            color = next(self.color)
            label = k
            v['category'] = category
            data.append([color, label])
            category+=1
        return pd.DataFrame(data, index=index, columns=columns)

class Image(DataFrameCollection):
    PRIVATE_KEYS = DataFrameCollection.PRIVATE_KEYS + ['/shape', '/category']
    SHAPE_CLASS = {
        'LineShape' : LineShape,
    }
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)

    def shape(self, k):
        return self.__class__.SHAPE_CLASS[self.df['/shape'].loc[k]['shape_class']]

    def category(self, k):
        return self.df['/category'].loc[k]

    def load(self, path):
        super(Image, self).load(path)
        # Check format
        for k,v in self.items():
            shape = self.shape(k)
            for kk in shape.shape_fields:
                assert kk in v.columns
            for category in np.unique(v['category']):
                assert category in self.df['/category'].index.values

    def build(self, trace, shape=None, category=None):
        df = {}
        if shape is None:
            shape = DefaultShapeCollection(trace)
        assert isinstance(shape, ShapeCollection)
        df['/shape'] = shape.to_DataFrame()
        # TODO: in parallel
        for k, v in shape.items():
            logging.info('Building %s' % k)
            df[k] = pd.DataFrame(v(trace))
        self.df = df
        if category is None:
            category = DefaultCategory
        self.df['/category'] = DefaultCategory()(self)

    def line(self):
        def df(k):
            shape_fields = self.shape(k).shape_fields
            todrop = list(filter(lambda k : k not in shape_fields, self.df[k].columns))
            return self.df[k].drop(columns=todrop)
        line = pd.concat([df(k) for k in filter(lambda k: self.shape(k) is LineShape, self)])
        line['category'] = line['category'].astype('category')
        color_map = {category : self.category(category)['color'] for category in np.unique(line['category'])}
        label_map = {category : self.category(category)['label'] for category in np.unique(line['category'])}
        return line, color_map, label_map
