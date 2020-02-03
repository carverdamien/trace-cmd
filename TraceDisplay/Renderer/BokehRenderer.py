from bokeh.plotting import figure
from bokeh.io import show, push_notebook, output_notebook
from bokeh.models import CustomJS, ColumnDataSource
from ipywidgets import interact_manual
import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd

output_notebook()

BOKEH_RENDERER = {}
FIGURE_RANGE_JSCODE = """
var brid = "%r";
var ax   = "%r";
var notebook = Jupyter.notebook;
var start = cb_obj.start;
var end = cb_obj.end;

notebook.kernel.execute("BOKEH_RENDERER["+brid+"].figure_range(ax="+ax+",start="+start+",end="+end+")");
"""

class BokehRenderer(object):
    def __init__(self, *args, **kwargs):
        x_range = (0,1)
        y_range = (0,1)
        # TODO: lock BOKEH_RENDERER
        global BOKEH_RENDERER
        self.brid = str(len(BOKEH_RENDERER))
        BOKEH_RENDERER[self.brid] = self
        # TODO: unlock BOKEH_RENDERER
        self.figure = figure(
            x_range = x_range,
            y_range = y_range,
            sizing_mode='stretch_both',
        )
        self._figure_range = {
            'x': {'start':x_range[0], 'end':x_range[1]},
            'y': {'start':y_range[0], 'end':y_range[1]},
        }
        self.figure.x_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'x'))
        self.figure.y_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'y'))
        self.notebook_handle = None
        df = pd.DataFrame({
            'x0' : [0],
            'x1' : [1],
            'y0' : [0],
            'y1' : [1],
            'c'  : [0],
        })
        df['c'] = df['c'].astype('category')
        self.lines = df
        self.color_key = ['#000000']
        image = self.updateImage()
        xmin, xmax = self.figure.x_range.start, self.figure.x_range.end
        ymin, ymax = self.figure.y_range.start, self.figure.y_range.end
        x_range = (xmin, xmax)
        y_range = (ymin, ymax)
        dw, dh = xmax - xmin, ymax - ymin
        self.source = ColumnDataSource(data=dict(image=[image.data], x=[xmin],
                                                 y=[ymin], dw=[dw], dh=[dh]))
        self.renderer = self.figure.image_rgba(source=self.source,
                                               image='image',
                                               x='x',
                                               y='y',
                                               dw='dw',
                                               dh='dh',
                                               dilate=False,
        )
        pass

    def updateImage(self):
        plot_width, plot_height = self.figure.plot_width, self.figure.plot_height
        xmin, xmax = self.figure.x_range.start, self.figure.x_range.end
        ymin, ymax = self.figure.y_range.start, self.figure.y_range.end
        x_range = (xmin, xmax)
        y_range = (ymin, ymax)
        dw, dh = xmax - xmin, ymax - ymin
        cvs = ds.Canvas(
            plot_width=plot_width,
            plot_height=plot_height,
            x_range=x_range,
            y_range=y_range,
        )
        agg = cvs.line(self.lines,
                       x=['x0','x1'], y=['y0','y1'],
                       agg=ds.count_cat('c'), axis=1,
        )
        image = tf.shade(agg,
                         min_alpha=255,
                         color_key=self.color_key
        )
        return image

    """ Callback in FIGURE_RANGE_JSCODE """
    def figure_range(self, ax=None, start=None, end=None):
        self._figure_range[ax].update({
            'start':start,
            'end':end,
        })

    def update(self):
        self.figure.x_range.start = self._figure_range['x']['start']
        self.figure.x_range.end = self._figure_range['x']['end']
        self.figure.y_range.start = self._figure_range['y']['start']
        self.figure.y_range.end = self._figure_range['y']['end']
        # TODO:
        print(self.figure.x_range.start, self.figure.x_range.end)
        print(self.figure.y_range.start, self.figure.y_range.end)
        xmin, xmax = self.figure.x_range.start, self.figure.x_range.end
        ymin, ymax = self.figure.y_range.start, self.figure.y_range.end
        x_range = (xmin, xmax)
        y_range = (ymin, ymax)
        dw, dh = xmax - xmin, ymax - ymin
        image = self.updateImage()
        self.source.data.update(
            dict(image=[image.data], x=[x_range[0]],
                        y=[y_range[0]], dw=[dw], dh=[dh])
        )
        push_notebook(handle=self.notebook_handle)
        pass

    def show(self):
        self.notebook_handle = show(self.figure, notebook_handle=True)
        interact_manual(self.update)
