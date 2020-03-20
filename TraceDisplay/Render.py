#!/usr/bin/env python2.7
import numpy as np
from Image import Image

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
    mpl_render('./img.png', './img.h5')
    # main('./rqsize.png', './rqsize.h5')
