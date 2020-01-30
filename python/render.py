#!/usr/bin/env python2.7
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

def main(render_path, data_path):
    with pd.HDFStore(data_path) as store:
        image = {
            k : store[k]
            for k in store.keys()
        }
        # TODO: handle other shapes than lines
        # print(image)
        xmin = min([min(min(image[line]['x0']), min(image[line]['x1'])) for line in image])
        xmax = max([max(max(image[line]['x0']), max(image[line]['x1'])) for line in image])
        ymin = min([min(min(image[line]['y0']), min(image[line]['y1'])) for line in image])
        ymax = max([max(max(image[line]['y0']), max(image[line]['y1'])) for line in image])
        ymin -= 1
        ymax += 1
        ypixels = len(np.unique(np.concatenate([np.unique([image[line]['y0'],image[line]['y1']]) for line in image])))
        scale = 2.
        dpi = scale*ypixels
        figsize = (6.4*dpi/100., 4.8*dpi/100.)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        for line in image:
            X0 = image[line]['x0'].values
	    X1 = image[line]['x1'].values
	    Y0 = image[line]['y0'].values
	    Y1 = image[line]['y1'].values
            L = np.transpose(np.array([[X0,X1],[Y0,Y1]]))
            # lc = LineCollection(L,color=category[c]['color'],label=category[c]['label'])
            lc = LineCollection(L,label=line,color='#000000')
            ax.add_collection(lc)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        fig.savefig(render_path)
    pass

if __name__ == '__main__':
    main('./rqsize.png', './rqsize.h5')
