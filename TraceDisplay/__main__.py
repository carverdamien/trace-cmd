import unittest, os, re, logging
from Trace import Trace
from Image import Image

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
            t = Trace()
            t.load(trace_path)
            print(t.timeline(0, 10))
            t.save(hdf_path)
            i = Image()
            i.build(t)
            i.save(img_path)
            count += 1
        self.assertTrue(count>0)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
