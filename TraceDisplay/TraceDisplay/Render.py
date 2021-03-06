import numpy as np
from .Image import Image
import logging

def bokeh_render(render_path, image):
    from bokeh.document import Document
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    from TraceDisplay import BokehRenderer

    bkr = BokehRenderer()
    bkr.render(image)

    doc = Document()
    doc.add_root(bkr.root)
    doc.validate()
    with open(render_path, "w") as f:
        f.write(file_html(doc, INLINE, render_path))
    logging.info("Wrote %s" % render_path)
    return file_html(doc, INLINE, render_path)
    pass

def plotly_render(render_path, image):
    import plotly.graph_objs as go
    from plotly.offline import plot

    line, color_map, label_map = image.line()

    def data(category):
        q = line.query('category == %d' % (category))
        N = len(q)
        X0 = q['x0'].values
        X1 = q['x1'].values
        Y0 = q['y0'].values
        Y1 = q['y1'].values

        x = np.empty(3*N)
        x[:] = np.nan
        x[0:(3*N)-2:3] = X0
        x[1:(3*N)-1:3] = X1

        y = np.empty(3*N)
        y[:] = np.nan
        y[0:(3*N)-2:3] = Y0
        y[1:(3*N)-1:3] = Y1

        return go.Scattergl(
            x=x, y=y, mode='lines',
            line=dict(color=color_map[category]),
            name=label_map[category]
        )

    fig = go.Figure(
        data=[
            data(category)
            for category in np.unique(line['category'])
        ]
    )

    plot(fig, filename=render_path, auto_open=False)
    pass

def mpl_render(render_path, image):
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    # print(image)
    line, color_map, label_map = image.line()
    if len(line) == 0:
        raise Exception('TODO: len(line) == 0')
    #print(line)
    xmin = min(min(line['x0']), min(line['x1']))
    xmax = max(max(line['x0']), max(line['x1']))
    ymin = min(min(line['y0']), min(line['y1']))
    ymax = max(max(line['y0']), max(line['y1']))
    # ymin -= 1
    # ymax += 1
    ypixels = len(np.unique(np.concatenate([np.unique(line[y]) for y in ['y0', 'y1']])))
    dpi = 100
    figsize = (6.4, 4.8)
    # print(dpi, ypixels)
    if dpi < ypixels:
        dpi = ypixels
    if not dpi % ypixels == 0:
        logging.warning('TODO')
    # scale = 160.
    # dpi = scale*ypixels
    # dpisqrt = np.sqrt(100./dpi)
    # figsize = (6.4*dpisqrt, 4.8*dpisqrt)
    # print(ypixels, figsize, dpi)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    # fig, ax = plt.subplots()
    for category in np.unique(line['category']):
        # print(category, color_map, label_map)
        q = line.query('category == %d' % (category))
        X0 = q['x0'].values
        X1 = q['x1'].values
        Y0 = q['y0'].values
        Y1 = q['y1'].values
        L = np.transpose(np.array([[X0,X1],[Y0,Y1]]))
        # lc = LineCollection(L,color=category[c]['color'],label=category[c]['label'])
        lc = LineCollection(L, label=label_map[category], color=color_map[category])
        ax.add_collection(lc)
    ax.legend()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    fig.savefig(render_path)
    pass
