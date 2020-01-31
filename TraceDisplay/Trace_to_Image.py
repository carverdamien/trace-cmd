#!/usr/bin/env python2.7
import logging
import os
from Trace import Trace
from Image import Image, Shapes_from

def main(image_path, trace_path, shape_paths):
    shapes = []
    for shape_path in shape_paths:
        shapes += Shapes_from(shape_path)
    if len(shapes) == 0:
        logging.error('No shapes where found')
        sys.exit(1)
    else:
        for shape in shapes:
            logging.info('Found shape %s' % shape[0])
        logging.info('Found %d shapes' % len(shapes))
    t = Trace()
    t.load(trace_path)
    i = Image()
    i.build(t, shapes)
    i.save(image_path)
    pass

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Build shapes from trace, following shape building rules, and save the shapes in an image file as pandas dataframes.",
    )
    parser.add_argument("image_path",
                        type=str,
                        help="path to the image output file",
    )
    parser.add_argument("trace_path",
                        type=str,
                        help="path to trace intput file (perfer .h5 over .dat)",
    )
    parser.add_argument("shape_paths",
                        type=str,
                        nargs='+',
                        help="paths to the shape building rules",
    )
    parser.add_argument("--force","-f",
                        action="store_true",
                        help="ignore checks. overwrite output file if it already exists",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    for path in [args.trace_path] + args.shape_paths:
        if not os.path.exists(path):
            logging.error('Cannot find %s' % path)
            sys.exit(1)
    if not args.force:
        for paths, ext in [
                [[args.trace_path, args.image_path],'.h5'],
                [args.shape_paths, '.py'],
        ]:
            for path in paths:
                if os.path.splitext(path)[1] != ext:
                    logging.warn('%s extension should be %s' % (path,ext))
        if os.path.exists(args.image_path):
            logging.error('File %s exists' % args.image_path)
            sys.exit(1)
    main(args.image_path,
         args.trace_path,
         args.shape_paths,
    )
