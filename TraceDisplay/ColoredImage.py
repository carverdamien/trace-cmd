from Image import Image
import pandas as pd
import numpy as np

class ColoredImage(Image):
    def __init__(self, image, inplace=True, *args, **kwargs):
        super(ColoredImage, self).__init__(*args, **kwargs)
        self.color_map = { 0 : '#000000' }
        if inplace:
            df = image.df
        else:
            df = image.df.copy()
        for k in df:
            assert 'color' not in df[k]
            df[k]['color'] = 0
            df[k]['color'] = df[k]['color'].astype('category')
        self.df = df
        self.line_and_color_key = None

    def get_line_and_color_key(self):
        if self.line_and_color_key is not None:
            return self.line_and_color_key
        def drop(df):
            todrop = list(filter(lambda k : k not in ['x0','x1','y0','y1', 'color'], df.columns))
            return df.drop(columns=todrop)
        line = pd.concat([drop(self.df[k]) for k in self.df])
        color_key = [self.color_map[color] for color in np.unique(line['color'])]
        self.line_and_color_key = line, color_key
        return self.line_and_color_key
