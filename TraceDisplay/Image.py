from .DataFrameCollection import DataFrameCollection, MetaDataFrame, FileExtensionError
import os
import logging
import pandas as pd
import numpy as np
import itertools
import json

SHAPE_FIELD = {
    # TODO: 'PointShape' : ['x','y','category'],
    'LineShape' : ['x0','x1','y0','y1','category'],
}

class ShapeDataFrame(MetaDataFrame):
    """docstring for ShapeDataFrame"""
    ATTR = 'shape'
    KEY  = '/shape'
    def __init__(self, dfc, df=pd.DataFrame()):
        super(ShapeDataFrame, self).__init__(dfc, df)
    def __setitem__(self, i, v):
        assert isinstance(i, int)
        assert i <= len(self.df)
        shape_class = v['shape_class']
        shape_field = v['shape_field']
        active      = v.get('active', True)
        if isinstance(shape_field, str):
            shape_field_str = shape_field
            shape_field_dict = json.loads(shape_field)
        if isinstance(shape_field, dict):
            shape_field_dict = shape_field
            shape_field_str = json.dumps(shape_field)
        assert isinstance(shape_class, str)
        assert isinstance(active, bool)
        assert isinstance(shape_field_dict, dict)
        assert isinstance(shape_field_str, str)
        assert shape_class in SHAPE_FIELD
        for k in shape_field_dict:
            assert k in self.dfc
            for field in SHAPE_FIELD[shape_class]:
                assert field in shape_field_dict[k]
                assert isinstance(shape_field_dict[k][field], str)
        item = dict(
            shape_class=shape_class,
            shape_field=shape_field_str,
            active=active,
        )
        super(ShapeDataFrame, self).__setitem__(i,item)

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

class CategoryDataFrame(MetaDataFrame):
    """docstring for CategoryDataFrame"""
    ATTR = 'category'
    KEY  = '/category'
    def __init__(self, dfc, df=pd.DataFrame()):
        super(CategoryDataFrame, self).__init__(dfc, df)
    def apply(self):
        for i in self:
            if not self[i]['active']:
                continue
            field = self[i]['field']
            query_dict = json.loads(self[i]['query'])
            for k in query_dict:
                if field not in self.dfc[k].columns:
                    # Inititalize
                    self.dfc.__getitem__(k,inplace=True)[field] = -1
                if query_dict[k]:
                    self.dfc.loc[k, self.dfc.eval(k, query_dict[k]), [field]] = i
                else:
                    self.dfc.loc[k, self.dfc.eval(k, 'index'), [field]] = i
    def __setitem__(self, i, v):
        assert isinstance(i, int)
        assert i <= len(self.df)
        label  = v['label']
        color  = v['color']
        field  = v['field']
        query  = v['query']
        active = v.get('active', True)
        if isinstance(query, str):
            query_str = query
            query_dict = json.loads(query)
        if isinstance(query, dict):
            query_dict = query
            query_str = json.dumps(query)
        assert isinstance(active, bool)
        assert isinstance(label, str)
        assert isinstance(color, str)
        assert isinstance(query_dict, dict)
        assert isinstance(query_str, str)
        for k in query_dict:
            assert k in self.dfc
            assert isinstance(query_dict[k], str)
        super(CategoryDataFrame, self).__setitem__(
            i,
            dict(
                label=label,
                color=color,
                field=field,
                query=query_str,
                active=active,
            ),
        )
    def append(self, label, color, field, query, active=True):
        # TODO: RM this function
        super(CategoryDataFrame, self).append(dict(
            label=label,
            color=color,
            field=field,
            query=query,
            active=active,
        ))

class Image(DataFrameCollection):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        CategoryDataFrame(self)
        ShapeDataFrame(self)

    def load(self, path):
        super(Image, self).load(path)
        # Check format
        for k, shape in self.shape.df.iterrows():
            shape_class = shape['shape_class']
            assert shape_class in SHAPE_FIELD
            shape_field = json.loads(shape['shape_field'])
            for k in shape_field:
                assert k in self
                for field in SHAPE_FIELD[shape_class]:
                    assert field in shape_field[k]

    def build(self, trace, shape=None, category=None, color=None):
        # TODO: rename build from_trace
        if shape is not None:
            raise Exception('TODO')
        for k,v in trace.items():
            assert v.index.name == 'timestamp'
            assert 'cpu' in v.columns
        for k in trace:
            self[k] = trace[k]
        for k in trace:
            shape = {
                'shape_class' : 'LineShape',
                'active' : True,
                'shape_field' : {k:{
                    'x0':'timestamp',
                    'y0':'cpu',
                    'x1':'timestamp',
                    'y1':'cpu + 0.5',
                    'category':'line0_category',
                }}
            }
            self.shape.append(shape)
        ccolor = itertools.cycle(DEFAULT_COLOR_VALUE)
        if category is not None:
            raise Exception('TODO')
        for k in trace:
            label = k
            color = next(ccolor)
            field = 'line0_category'
            query = json.dumps({k:''})
            active = True
            self.category.append(label, color, field, query, active)

    def line(self):
        def empty():
            return pd.DataFrame({
                'x0' : [],
                'x1' : [],
                'y0' : [],
                'y1' : [],
                'category' : [],
            })
        def build(i, line):
            if not line['active']:
                return empty()
            shape_field = json.loads(line['shape_field'])
            if len(shape_field) == 0:
                logging.warn(f'shape {i} is empty')
                return empty()
            return pd.concat([pd.DataFrame({
                'x0' : np.array(self.eval(k,shape_field[k]['x0']).values, dtype=float),
                'x1' : np.array(self.eval(k,shape_field[k]['x1']).values, dtype=float),
                'y0' : np.array(self.eval(k,shape_field[k]['y0']).values, dtype=float),
                'y1' : np.array(self.eval(k,shape_field[k]['y1']).values, dtype=float),
                'category' : np.array(self.eval(k,shape_field[k]['category']).values, dtype=int),
            }) for k in shape_field])
        self.category.apply()
        sel_line = self.shape.df['shape_class'] == 'LineShape'
        lineshape = self.shape.df[sel_line]
        line = pd.concat([build(i,r) for i,r in lineshape.iterrows()], sort=True)
        line.loc[:,['category']] = line['category'].astype('category')
        category = np.unique(line['category'])
        color_map = {c : self.category[c]['color'] for c in category}
        label_map = {c : self.category[c]['label'] for c in category}
        return line, color_map, label_map
