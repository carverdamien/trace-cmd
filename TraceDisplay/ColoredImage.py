from Image import Image
import pandas as pd
import numpy as np
import itertools

class ColoredImage(Image):
    def __init__(self, image, inplace=True, *args, **kwargs):
        super(ColoredImage, self).__init__(*args, **kwargs)
        # From https://repository.lboro.ac.uk/articles/Categorical_colormap_optimization_with_visualization_case_studies/9401987/files/17018552.pdf
        self.color_map = {
            0  : '#660066',
            1  : '#006633',
            2  : '#FFCC00',
            3  : '#CC3333',
            4  : '#996633',
            5  : '#000099',
            6  : '#000000',
            7  : '#0099CC',
            8  : '#868F98',
            9  : '#009999',
            10 : '#CC9999',
            11 : '#66CCCC',
            12 : '#66CC00',
            13 : '#FF6600',
        }
        if inplace:
            df = image.df
        else:
            df = image.df.copy()
        color = itertools.cycle(list(self.color_map.keys()))
        for k in df:
            assert 'color' not in df[k]
            df[k]['color'] = next(color)
        self.df = df
        self.line_and_color_key = None

    def get_line_and_color_key(self):
        if self.line_and_color_key is not None:
            return self.line_and_color_key
        def drop(df):
            todrop = list(filter(lambda k : k not in ['x0','x1','y0','y1', 'color'], df.columns))
            return df.drop(columns=todrop)
        line = pd.concat([drop(self.df[k]) for k in self.df])
        line['color'] = line['color'].astype('category')
        color_key = [self.color_map[color] for color in np.unique(line['color'])]
        self.line_and_color_key = line, color_key
        return self.line_and_color_key
