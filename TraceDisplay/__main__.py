import unittest, os, re, logging
import numpy as np
import pandas as pd
from Trace import Trace
from Image import Image
from Render import mpl_render, plotly_render, bokeh_render
from DataFrameCollection import DataFrameCollection

NR_SCALE = 10

def find(walk_path, path_match='.*'):
    match = re.compile(path_match)
    for dirpath, dirnames, filenames in os.walk(walk_path):
        for filename in filenames:
            to_match = os.path.join(dirpath, filename)
            print(to_match)
            if match.match(to_match):
                yield to_match

class TestTrace(unittest.TestCase):
    def test_load_and_save(self):
        WALK_PATH = os.environ.get('WALK_PATH', '.')
        count = 0
        for trace_path in find(WALK_PATH, '.*.dat$'):
            no_ext_path = os.path.splitext(trace_path)[0]
            hdf_path = no_ext_path + '.h5'
            img_path = no_ext_path + '.i.h5'
            mpl_render_path = no_ext_path + '.png'
            plotly_render_path = no_ext_path + '.plotly.html'
            bokeh_render_path = no_ext_path + '.bokeh.html'
            timeline_path = no_ext_path + '.csv'
            t = Trace()
            t.load(trace_path)
            t.timeline(0, 10).to_csv(timeline_path)
            t.save(hdf_path)
            i = Image()
            i.build(t)
            i.save(img_path)
            mpl_render(mpl_render_path, img_path)
            plotly_render(plotly_render_path, img_path)
            bokeh_render(bokeh_render_path, img_path)
            count += 1
        self.assertTrue(count>0)

def randomDataFrame(nr_rows=NR_SCALE, nr_cols=NR_SCALE, dtype=[int, float, str]):
    return pd.DataFrame({
        'col%d' % (c) : np.array(np.random.rand(nr_rows), dtype=dtype[np.random.randint(len(dtype))])
        for c in range(nr_cols)
    })

def randomDictOfDataFrame(nr_keys=NR_SCALE, nr_rows=NR_SCALE, nr_cols=NR_SCALE):
    return {
        'key%d' : randomDataFrame(nr_rows, nr_cols)
        for k in range(nr_keys)
    }

class TestDataFrameCollection(unittest.TestCase):
    def test_init(self):
        DataFrameCollection(randomDictOfDataFrame())
        pass
    def test_set_get(self):
        dfc = DataFrameCollection()
        for k,v in randomDictOfDataFrame().items():
            dfc[k] = v
            assert v is dfc[k]
        pass
    def test_set_fails_if_not_DataFrame(self):
        dfc = DataFrameCollection()
        def fails():
            dfc['foo'] = {}
        self.assertRaises(Exception, fails)
        pass
    def test_private_keys(self):
        i = Image()
        for k in Image.PRIVATE_KEYS:
            def set_fails():
                i[k] = randomDataFrame()
            self.assertRaises(Exception, set_fails)
            def get_fails():
                foo = i[k]
            self.assertRaises(Exception, get_fails)
        pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
