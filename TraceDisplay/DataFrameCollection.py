import pandas as pd
import os
import logging

class DataFrameCollection(object):
    def __init__(self,dict_of_data_frames={}):
        assert isinstace(dict_of_data_frames, dict)
        for k,v in dict_of_data_frames:
            assert isinstace(v, pd.DataFrame)
        self.__df = dict_of_data_frames

    def __getitem__(self, k):
        return self.__df[k]

    def keys(self):
        return self.__df.keys()

    def save(self, hdf_path):
        if os.path.exists(hdf_path):
            logging.info('Overwriting %s' % hdf_path)
            os.remove(hdf_path)
        for k,v in self.__df.items():
            logging.info('Saving %s' % k)
            v.to_hdf(hdf_path, key=k, mode='a')

    def load(self, hdf_path):
        with pd.HDFStore(hdf_path) as store:
            logging.info('Loading %s' % hdf_path)
            df = {}
            for k in store.keys():
                logging.info('Loading %s' % k)
                df[k] = store[k]
            self.__df = df
