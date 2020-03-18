import pandas as pd
import os
import logging

class FileExtensionError(Exception):
    def __init__(self, path=None, expected_extension=None):
        self.path = path
        self.expected_extension = expected_extension
    pass

class DataFrameCollection(object):
    def __init__(self,dict_of_data_frames={}):
        assert isinstance(dict_of_data_frames, dict)
        for k,v in dict_of_data_frames:
            assert isinstance(v, pd.DataFrame)
        self.df = dict_of_data_frames

    def __getitem__(self, k):
        kk = '/'+str(k)
        if k not in self.df and kk in self.df:
            k = kk
        return self.df[k]

    def __setitem__(self, k, v):
        assert isinstance(v, pd.DataFrame)
        self.df[k] = v

    def __len__(self):
        return len(self.df)

    def __delitem__(self, k):
        del self.df[k]

    def __iter__(self):
        return iter(self.df)

    def __contains__(self, v):
        return v in self.df

    def values(self):
        return self.df.values()

    def items(self):
        return self.df.items()

    def keys(self):
        return self.df.keys()

    def save(self, hdf_path):
        if os.path.splitext(hdf_path)[1] != '.h5':
            raise FileExtensionError(hdf_path, '.h5')
        if os.path.exists(hdf_path):
            logging.info('Overwriting %s' % hdf_path)
            os.remove(hdf_path)
        if len(self.df) == 0:
            logging.warn('Will not save empty DataFrameCollection')
        for k,v in self.df.items():
            logging.info('Saving %s' % k)
            v.to_hdf(hdf_path, key=k, mode='a')

    def load(self, hdf_path):
        if os.path.splitext(hdf_path)[1] != '.h5':
            raise FileExtensionError(hdf_path, '.h5')
        with pd.HDFStore(hdf_path) as store:
            logging.info('Loading %s' % hdf_path)
            df = {}
            for k in store.keys():
                logging.info('Loading %s' % k)
                df[k] = store[k]
            self.df = df
