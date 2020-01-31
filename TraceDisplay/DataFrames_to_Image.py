#!/usr/bin/env python2.7
import pandas as pd
import logging
import os
from Trace_to_DataFrames import DataFrames_to_hdf

def Shapes_from(shape_path):
    logging.info('Reading %s' % shape_path)
    new_globals = {}
    new_locals = {}
    execfile(shape_path, new_globals, new_locals)
    if 'SHAPES' in new_locals:
        SHAPES = new_locals['SHAPES']
        assert isinstance(SHAPES, dict)
        SHAPES = SHAPES.items()
    else:
        # Every function is a shape rule
        SHAPES = list(filter(
            lambda i : callable(i[1]),
            new_locals.items())
        )
    for k,v in SHAPES:
        assert isinstance(k, str)
        assert callable(v)
    return SHAPES

def DataFrames_to_Image(df, shapes):
    image = {}
    # TODO: in parallel
    for name, func in shapes:
        logging.info('Building %s' % name)
        image[name] = pd.DataFrame(func(df))
    return image

def main(image_path, data_path, shape_paths):
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
    with pd.HDFStore(data_path) as store:
        logging.info('Loading %s' % data_path)
        df = {
            k:store[k]
            for k in store.keys()
        }
        image = DataFrames_to_Image(df, shapes)
        DataFrames_to_hdf(image, image_path)
    pass

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Build shapes from data stored as pandas dataframes, following shape building rules, and save the shapes in an image file as pandas dataframes.",
    )
    parser.add_argument("image_path",
                        type=str,
                        help="path to the image output file",
    )
    parser.add_argument("data_path",
                        type=str,
                        help="path to the pandas dataframes intput file",
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
    for path in [args.data_path] + args.shape_paths:
        if not os.path.exists(path):
            logging.error('Cannot find %s' % path)
            sys.exit(1)
    if not args.force:
        for paths, ext in [
                [[args.data_path, args.image_path],'.h5'],
                [args.shape_paths, '.py'],
        ]:
            for path in paths:
                if os.path.splitext(path)[1] != ext:
                    logging.warn('%s extension should be %s' % (path,ext))
        if os.path.exists(args.image_path):
            logging.error('File %s exists' % args.image_path)
            sys.exit(1)
    main(args.image_path,
         args.data_path,
         args.shape_paths,
    )
