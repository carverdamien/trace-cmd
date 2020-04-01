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
import logging

BOKEH_RENDERER = {}
FIGURE_RANGE_JSCODE = """
if (typeof Jupyter !== 'undefined') {
var brid = "%r";
var ax   = "%r";
var notebook = Jupyter.notebook;
var start = cb_obj.start;
var end = cb_obj.end;

notebook.kernel.execute("BOKEH_RENDERER["+brid+"].figure_range(ax="+ax+",start="+start+",end="+end+")");
}
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
            active_scroll = 'wheel_zoom',
            sizing_mode='stretch_both',
        )
        self.legend = Div(
            visible=True,
            height_policy='fit',
        )
        self.root = row(self.figure, self.legend, sizing_mode='stretch_both')
        self._figure_range = {
            'x': {'start':x_range[0], 'end':x_range[1]},
            'y': {'start':y_range[0], 'end':y_range[1]},
        }
        self.figure.x_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'x'))
        self.figure.y_range.callback = CustomJS(code=FIGURE_RANGE_JSCODE % (self.brid, 'y'))
        self.notebook_handle = None
        self.image_model = None
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

    def push_notebook(self):
        if self.notebook_handle:
            push_notebook(handle=self.notebook_handle)

    def update_model(self):
        line, color_map, label_map = self.image_model.line()
        xmin = min(min(line['x0']), min(line['x1']))
        xmax = max(max(line['x0']), max(line['x1']))
        ymin = min(min(line['y0']), min(line['y1']))
        ymax = max(max(line['y0']), max(line['y1']))
        self.figure.x_range.reset_start = xmin
        self.figure.x_range.reset_end   = xmax
        self.figure.y_range.reset_start = ymin
        self.figure.y_range.reset_end   = ymax
        return line, color_map, label_map

    def render(self, image_model):
        assert isinstance(image_model, Image)
        self.image_model = image_model
        self.update_all(reset_ranges=True)

    def update_image(self, size, ranges, line, color_map):
        plot_width, plot_height = size
        x_range, y_range = ranges
        xmin, xmax = x_range
        ymin, ymax = y_range
        dw, dh = xmax - xmin, ymax - ymin
        color_key = [color_map[k] for k in sorted(color_map.keys())]
        image = self.rendering(line, xmin, xmax, ymin, ymax, plot_width, plot_height, color_key)
        self.image = image
        self.source.data.update(dict(image=[image.data],
                                     x=[xmin],
                                     y=[ymin],
                                     dw=[dw],
                                     dh=[dh])
        )
        pass

    def update_legend(self, color_map, label_map):
        text = ''.join(['<ul style="list-style: none;padding-left: 0;">'] +
            [
                '<li><span style="color: %s;">%d %s</span></li>' % (color_map[c], c, label_map[c])
                for c in color_map
            ] + ['</ul>']
        )
        text = '<div style="overflow:scroll; max-height: 45em;">'+ text +'</div>'
        self.legend.text = text

    """ Callback in FIGURE_RANGE_JSCODE """
    def figure_range(self, ax=None, start=None, end=None):
        self._figure_range[ax].update({
            'start':start,
            'end':end,
        })

    def update_ranges(self, reset_ranges=False, notify_update=True):
        if reset_ranges:
            self._figure_range['x']['start'] = self.figure.x_range.reset_start
            self._figure_range['x']['end']   = self.figure.x_range.reset_end
            self._figure_range['y']['start'] = self.figure.y_range.reset_start
            self._figure_range['y']['end']   = self.figure.y_range.reset_end
        xmin = self.figure.x_range.start = self._figure_range['x']['start']
        xmax = self.figure.x_range.end   = self._figure_range['x']['end']
        ymin = self.figure.y_range.start = self._figure_range['y']['start']
        ymax = self.figure.y_range.end   = self._figure_range['y']['end']
        if notify_update:
            for func in self.notify_update:
                func(xmin,xmax,ymin,ymax)
        return ((xmin,xmax),(ymin,ymax))

    def update(self):
        self.update_all()

    def update_all(self, push_notebook=True, reset_ranges=False):
        if self.image_model is None:
            logging.error('Missing image model')
            return
        line, color_map, label_map = self.update_model()
        size = self.figure.plot_width, self.figure.plot_height
        ranges = self.update_ranges(reset_ranges=reset_ranges)
        self.update_image(size, ranges, line, color_map)
        self.update_legend(color_map, label_map)
        if push_notebook:
            self.push_notebook()
        pass

    def show(self):
        output_notebook(hide_banner=True)
        self.notebook_handle = show(self.root, notebook_handle=True)
        interact_manual(self.update)

    def to_html(self):
        return file_html(self.root, INLINE, '')