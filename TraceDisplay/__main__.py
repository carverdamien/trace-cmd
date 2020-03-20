import unittest, os, re, logging
import numpy as np
from Trace import Trace
from Image import Image
from Render import render
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
            hdf_path = os.path.splitext(trace_path)[0] + '.h5'
            img_path = os.path.splitext(trace_path)[0] + '.i.h5'
            render_path = os.path.splitext(trace_path)[0] + '.png'
            t = Trace()
            t.load(trace_path)
            print(t.timeline(0, 10))
            t.save(hdf_path)
            i = Image()
            i.build(t)
            i.save(img_path)
            print(i.line())
            render(render_path, img_path)
            count += 1
        self.assertTrue(count>0)

def randomDataFrame(nr_rows=NR_SCALE, nr_cols=NR_SCALE, dtype=[int, float, str]):
    return pd.DataFrame({
        'col%d' % (c) : np.array(np.random.rand(nr_rows), dtype=dtype[np.random.randint(len(dtype))])
        for c in range(nr_cols)
    })

def randomDictOfDataFrame(nr_keys=NR_SCALE, nr_rows=NR_SCALE, nr_cols=NR_SCALE):
    return {
        'key%d' : randomDataFrame(nr_rows, nr_col)
        for k in range(nr_keys)
    }

class TestDataFrameCollection(unittest.TestCase):
    def test_init(self):
        DataFrameCollection(randomDictOfDataFrame())
        pass
    def test_set_get(self):
        dfc = DataFrameCollection()
        for k,v in randomDictOfDataFrame():
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
