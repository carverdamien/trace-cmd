import unittest, os, re

def find(walk_path, path_match='.*'):
    match = re.compile(path_match)
    for dirpath, dirnames, filenames in os.walk(walk_path):
        for filename in filenames:
            to_match = os.path.join(dirpath, filename)
            if match.match(to_match):
                yield to_match

class TestTrace(unittest.TestCase):
    def test_load_and_save(self):
        for trace_path in find('.', '.*.dat'):
            hdf_path = os.path.splitext(trace_path)[1] + '.h5'
            t = Trace()
            t.load(trace_path)
            t.save(hdf_path)

if __name__ == '__main__':
    unittest.main()
