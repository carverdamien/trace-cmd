from .DataFrameCollection import DataFrameCollection, MetaDataFrame, FileExtensionError
import os
import logging
import pandas as pd
import numpy as np
import itertools
import json

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

SHAPE_CLASS = {
    'LineShape' : LineShape,
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
        columns = ['color', 'label', 'query']
        category = 0
        for k in image:
            index.append(category)
            color = next(self.color)
            label = k
            query = json.dumps({k:'category != %d' % category})
            data.append([color, label, query])
            category+=1
        return pd.DataFrame(data, index=index, columns=columns)

class ShapeDataFrame(MetaDataFrame):
    """docstring for ShapeDataFrame"""
    ATTR = 'shape'
    KEY  = '/shape'
    def __init__(self, dfc, df=pd.DataFrame()):
        super(ShapeDataFrame, self).__init__(dfc, df)
    def __setitem__(self, k, v):
        assert k in self.dfc
        assert v in SHAPE_CLASS
        shape_class = SHAPE_CLASS[v]
        for field in shape_class.shape_fields:
            assert field in self.dfc[k].columns
        super(ShapeDataFrame, self).__setitem__(k,{'shape_class':v})
    def __getitem__(self, k):
        return  super(ShapeDataFrame, self).__getitem__(k)['shape_class']

class CategoryDataFrame(MetaDataFrame):
    """docstring for CategoryDataFrame"""
    ATTR = 'category'
    KEY  = '/category'
    def __init__(self, dfc, df=pd.DataFrame()):
        super(CategoryDataFrame, self).__init__(dfc, df)
    def __setitem__(self, k, v):
        assert isinstance(k, int)
        assert k == len(self.df)
        super(CategoryDataFrame, self).__setitem__(k, v)
    def append(self, label, color, query):
        if isinstance(query, str):
            query_str = query
            query_dict = json.loads(query)
        if isinstance(query, dict):
            query_dict = query
            query_str = json.dumps(query)
        assert isinstance(label, str)
        assert isinstance(color, str)
        assert isinstance(query_dict, dict)
        assert isinstance(query_str, str)
        for k in query_dict:
            assert k in self.dfc
        i = len(self.df)
        for k in query_dict:
            self.dfc.loc[k, self.dfc.eval(k, query_dict[k]), ['category']] = i
        super(CategoryDataFrame, self).append({
            'label' : label,
            'color' : color,
            'query' : query_str,
        })

class Image(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        CategoryDataFrame(self)
        ShapeDataFrame(self)

    def load(self, path):
        super(Image, self).load(path)
        # Check format
        for k,v in self.items():
            shape_class = SHAPE_CLASS[self.shape[k]]
            for kk in shape_class.shape_fields:
                assert kk in v.columns
            for category in np.unique(v['category']):
                assert category in self.category

    def build(self, trace, shape=None, category=None):
        if shape is None:
            shape = DefaultShapeCollection(trace)
        else:
            raise Exception('TODO')
        assert isinstance(shape, ShapeCollection)
        # TODO: in parallel
        for k, v in shape.items():
            logging.info('Building %s' % k)
            self[k] = pd.DataFrame(v(trace))
            self.shape[k] = v.shape_class
        if category is None:
            category = DefaultCategory()(self)
        else:
            raise Exception('TODO')
        for i, c in category.iterrows():
            label = c['label']
            color = c['color']
            query = c['query']
            self.category.append(label, color, query)

    def line(self):
        def df(k):
            shape_fields = SHAPE_CLASS[self.shape[k]].shape_fields
            todrop = list(filter(lambda k : k not in shape_fields, self[k].columns))
            return self[k].drop(columns=todrop)
        line = pd.concat([df(k) for k in filter(lambda k: self.shape[k] == 'LineShape', self)])
        line['category'] = line['category'].astype('category')
        category = np.unique(line['category'])
        color_map = {c : self.category[c]['color'] for c in category}
        label_map = {c : self.category[c]['label'] for c in category}
        return line, color_map, label_map
