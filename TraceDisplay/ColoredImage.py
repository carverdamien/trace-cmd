from Image import Image

class ColoredImage(Image):
    def __init__(self, *args, image, inplace=True, **kwargs):
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
