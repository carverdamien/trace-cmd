# -*- coding: utf-8 -*-
from Image import Image
import pandas as pd
import numpy as np
import itertools

# From https://repository.lboro.ac.uk/articles/Categorical_colormap_optimization_with_visualization_case_studies/9401987/files/17018552.pdf
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

class Color(object):
    def __init__(self, category, value, label, query):
        self.category = category
        self.value = value
        self.label = label
        self.query = query

    def legend(self):
        return {
            'category' : self.category,
            'value'    : self.value,
            'label'    : self.label,
            'query'    : self.query,
        }

    def applyColor(self, df):
        assert isinstance(df, dict)
        for k,v in self.query.items():
            assert isinstance(df[k], pd.DataFrame)
            if v:
                df[k].query(v)['color'] = self.category
            else:
                df[k]['color'] = self.category

class ColoredImage(Image):
    def __init__(self, image, inplace=True, *args, **kwargs):
        super(ColoredImage, self).__init__(*args, **kwargs)
        # TODO: generator radom values if more values are needed
        self.color_category_generator = itertools.count(0)
        self.color_value_generator = itertools.cycle(DEFAULT_COLOR_VALUE)
        self.color_stack = []
        self.color_map = {}
        if inplace:
            df = image.df
        else:
            df = image.df.copy()
        for k in df:
            assert 'color' not in df[k]
            df[k]['color'] = float('NaN')
            self.addColor(label=k, query={k:''})
        self.df = df
        self.applyColor()
        self.line_and_color_key = None

    def addColor(self, category=None, value=None, label=None, query={}):
        if category is None:
            category = next(self.color_category_generator)
        if value is None:
            value = next(self.color_value_generator)
        c = Color(category, value, label, query)
        self.color_stack.append(c)
        self.color_map[category] = c
        return c

    def applyColor(self):
        for c in self.color_stack:
            c.applyColor(self.df)

    def get_line_and_color_key(self):
        if self.line_and_color_key is not None:
            return self.line_and_color_key
        def drop(df):
            todrop = list(filter(lambda k : k not in ['x0','x1','y0','y1', 'color'], df.columns))
            return df.drop(columns=todrop)
        line = pd.concat([drop(self.df[k]) for k in self.df])
        line['color'] = line['color'].astype('category')
        color_key = [self.color_map[color].value for color in np.unique(line['color'])]
        self.line_and_color_key = line, color_key
        return self.line_and_color_key

    def legend(self):
        return [
            c.legend()
            for c in self.color_stack
        ]

    def html_legend(self):
        return ''.join(['<ul style="list-style: none;padding-left: 0;">'] +
                       [
                           '<li><span style="color: {value};">{category} {label}</span></li>'.format(**e)
                           for e in self.legend()
                       ] +
                       ['</ul>']
        )
