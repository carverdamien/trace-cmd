from bokeh.plotting import figure
from bokeh.layouts import row
from bokeh.models.widgets import Div
from bokeh.embed import file_html
from bokeh.resources import INLINE
from bokeh.io import show, push_notebook, output_notebook
from bokeh.models import CustomJS, ColumnDataSource
from ipywidgets import interact_manual
import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import numpy as np
from ..Image import Image

BOKEH_RENDERER = {}
FIGURE_RANGE_JSCODE = """
var brid = "%r";
var ax   = "%r";
var notebook = Jupyter.notebook;
var start = cb_obj.start;
var end = cb_obj.end;

notebook.kernel.execute("BOKEH_RENDERER["+brid+"].figure_range(ax="+ax+",start="+start+",end="+end+")");
"""

def default_rendering(line, xmin, xmax, ymin, ymax, plot_width, plot_height, color_key):
    x_range = (xmin, xmax)
    y_range = (ymin, ymax)
    dw, dh = xmax - xmin, ymax - ymin
    cvs = ds.Canvas(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=x_range,
        y_range=y_range,
    )
    agg = cvs.line(line,
                   x=['x0','x1'],
                   y=['y0','y1'],
                   agg=ds.count_cat('category'),
                   axis=1,
    )
    image = tf.shade(agg,
                     min_alpha=255,
                     color_key=color_key,
    )
    return image

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
        self.legend = Div(
            visible=True,
            height_policy='max',
        )
        self.row = row(self.legend, self.figure, sizing_mode='stretch_both')
        self._figure_range = {
            'x': {'start':x_range[0], 'end':x_range[1]},
            'y': {'start':y_range[0], 'end':y_range[1]},
        }
        self.figure.x_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'x'))
        self.figure.y_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'y'))
        self.notebook_handle = None
        self.colored_image = None
        self.image = None
        self.rendering = default_rendering
        self.source = ColumnDataSource(data=dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.renderer = self.figure.image_rgba(source=self.source,
                                               image='image',
                                               x='x',
                                               y='y',
                                               dw='dw',
                                               dh='dh',
                                               dilate=False,
        )
        self.notify_update = []

    def reset_ranges(self):
        ci = self.colored_image
        xmin = min(min(np.min(ci[k]['x0']), np.min(ci[k]['x1'])) for k in ci)
        xmax = max(max(np.max(ci[k]['x0']), np.max(ci[k]['x1'])) for k in ci)
        ymin = min(min(np.min(ci[k]['y0']), np.min(ci[k]['y1'])) for k in ci)
        ymax = max(max(np.max(ci[k]['y0']), np.max(ci[k]['y1'])) for k in ci)
        self._figure_range.update({
            'x': {'start':xmin, 'end':xmax},
            'y': {'start':ymin, 'end':ymax},
        })

    def render(self, ci):
        assert isinstance(ci, Image)
        self.colored_image = ci
        self.reset_ranges()
        self.update()

    def updateImage(self):
        plot_width, plot_height = self.figure.plot_width, self.figure.plot_height
        xmin, xmax = self.figure.x_range.start, self.figure.x_range.end
        ymin, ymax = self.figure.y_range.start, self.figure.y_range.end
        x_range = (xmin, xmax)
        y_range = (ymin, ymax)
        dw, dh = xmax - xmin, ymax - ymin
        if self.colored_image is None:
            return
        line, color_map, label_map = self.colored_image.line()
        category = np.unique(line['category'])
        self.legend.text = ''.join(['<ul style="list-style: none;padding-left: 0;">'] +
            [
                '<li><span style="color: %s;">%d %s</span></li>' % (color_map[c], c, label_map[c])
                for c in category
            ] + ['</ul>']
        )
        push_notebook(handle=self.notebook_handle) # DEBUG # TODO: rm this line
        color_key = [color_map[k] for k in sorted(color_map.keys()) if k in category]
        image = self.rendering(line, xmin, xmax, ymin, ymax, plot_width, plot_height, color_key)
        self.image = image
        self.source.data.update(dict(image=[image.data],
                                     x=[xmin],
                                     y=[ymin],
                                     dw=[dw],
                                     dh=[dh])
        )
        pass

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
        # print(self.figure.x_range.start, self.figure.x_range.end)
        # print(self.figure.y_range.start, self.figure.y_range.end)
        # print(f"{self._figure_range}")
        # print(self.colored_image._df['/filter'])
        self.updateImage()
        push_notebook(handle=self.notebook_handle)
        for func in self.notify_update:
            func(self.figure.x_range.start,
                 self.figure.x_range.end,
                 self.figure.y_range.start,
                 self.figure.y_range.end,
            )
        pass

    def show(self):
        output_notebook(hide_banner=True)
        self.notebook_handle = show(self.row, notebook_handle=True)
        interact_manual(self.update)

    def to_html(self):
        return file_html(self.row, INLINE, '')