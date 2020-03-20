#!/usr/bin/env python2.7
import numpy as np
from Image import Image

def plotly_render(render_path, data_path):
    import plotly.graph_objs as go
    from plotly.offline import plot

    image = Image()
    image.load(data_path)
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

def mpl_render(render_path, data_path):
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    image = Image()
    image.load(data_path)
    # print(image)
    line, color_map, label_map = image.line()
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
    assert dpi % ypixels == 0
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

if __name__ == '__main__':
    import argparse, sys, os, logging
    parser = argparse.ArgumentParser(
        description="Render from image",
    )
    parser.add_argument("render_path",
                        type=str,
                        help="path to render output file",
    )
    parser.add_argument("image_path",
                        type=str,
                        help="path to the image input file",
    )
    parser.add_argument("--force","-f",
                        action="store_true",
                        help="ignore checks. overwrite output file if it already exists",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    if os.path.splitext(args.render_path)[1] == '.html':
        plotly_render(args.render_path, args.image_path)
    else:
        mpl_render(args.render_path, args.image_path)
