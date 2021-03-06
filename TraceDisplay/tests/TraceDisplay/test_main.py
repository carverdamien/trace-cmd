import unittest, os, re, logging
import numpy as np
import pandas as pd
from TraceDisplay import Trace, Image, DataFrameCollection
from TraceDisplay import mpl_render, plotly_render, bokeh_render

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
        for trace_path in find(WALK_PATH, '(.*.dat$)|(.*.dat.gz$)'):
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
            mpl_render(mpl_render_path, i)
            plotly_render(plotly_render_path, i)
            bokeh_render(bokeh_render_path, i)
            count += 1
        self.assertTrue(count>0)

def randomDataFrame(nr_rows=NR_SCALE, nr_cols=NR_SCALE, dtype=[int, float, str]):
    return pd.DataFrame({
        'col%d' % (c) : np.array(np.random.rand(nr_rows), dtype=dtype[np.random.randint(len(dtype))])
        for c in range(nr_cols)
    })

def randomDictOfDataFrame(nr_keys=NR_SCALE, nr_rows=NR_SCALE, nr_cols=NR_SCALE):
    return {
        'key%d' % (k) : randomDataFrame(nr_rows, nr_cols)
        for k in range(nr_keys)
    }

def seqDataFrame(nr_rows=NR_SCALE, nr_cols=NR_SCALE, dtype=[int, float]):
    return pd.DataFrame({
        'col%d' % (c) : np.arange(nr_rows, dtype=dtype[np.random.randint(len(dtype))])
        for c in range(nr_cols)
    })

def seqDictOfDataFrame(nr_keys=NR_SCALE, nr_rows=NR_SCALE, nr_cols=NR_SCALE):
    return {
        'key%d' % (k) : seqDataFrame(nr_rows, nr_cols)
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
            assert v.equals(dfc[k])
        pass
    def test_set_fails_if_not_DataFrame(self):
        dfc = DataFrameCollection()
        def fails():
            dfc['foo'] = {}
        self.assertRaises(Exception, fails)
        pass
    def test_private_keys(self):
        i = Image()
        for k in i.private_key:
            def set_fails():
                i[k] = randomDataFrame()
            self.assertRaises(Exception, set_fails)
            def get_fails():
                foo = i[k]
            self.assertRaises(Exception, get_fails)
        pass
    def test_filter(self):
        dfc = DataFrameCollection(seqDictOfDataFrame())
        for k in dfc:
            dfc.filter[k] = 'col0 == 0'
            self.assertEqual(len(dfc[k]), 1)
        dfc.filter.update({
            k : 'col0 == 0 | col0 == 1'
            for k in dfc
        })
        for k in dfc:
            self.assertEqual(len(dfc[k]), 2)
    def test_loc(self):
        dfc = DataFrameCollection(seqDictOfDataFrame())
        self.assertTrue(np.allclose(dfc.loc['/key0',[0],['col0']],0))
        dfc.loc['/key0',[0],['col0']] = -1
        self.assertTrue(np.allclose(dfc.loc['/key0',[0],['col0']],-1))
    def test_query(self):
        dfc = DataFrameCollection(seqDictOfDataFrame())
        for k in dfc:
            self.assertEqual(len(dfc.query(k, 'col0 == 0')), 1)
        for k,v in dfc.query({
            k : '(col0 == 0) | (col0 == 1)'
            for k in dfc
        }).items():
            self.assertEqual(len(v), 2)
    def test_eval(self):
        dfc = DataFrameCollection(seqDictOfDataFrame())
        for k in dfc:
            self.assertEqual(len(dfc.eval(k, 'col0[col0 == 0]')), 1)
        for k,v in dfc.eval({
            k : 'col0[(col0 == 0) | (col0 == 1)]'
            for k in dfc
        }).items():
            self.assertEqual(len(v), 2)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
