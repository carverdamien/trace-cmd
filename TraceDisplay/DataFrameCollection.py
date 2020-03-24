import pandas as pd
import os
import logging

class FileExtensionError(Exception):
    def __init__(self, path=None, expected_extension=None):
        message = "%s %s" %  (expected_extension, path)
        super(FileExtensionError, self).__init__(message)
        self.path = path
        self.expected_extension = expected_extension
    pass

class Loc(object):
    def __init__(self, df):
        self.df = df
    def __setitem__(self, k, v):
        k, i, c, = k
        self.df[k].loc[i,c] = v
    def __getitem__(self, k):
        k,i,c = k
        return self.df[k].loc[i,c]

class DataFrameCollection(object):
    PRIVATE_KEYS = ['/filter']
    def __init__(self,dict_of_data_frames={}):
        self._df = {}
        self.loc = Loc(self._df)
        assert isinstance(dict_of_data_frames, dict)
        for k,v in dict_of_data_frames.items():
            self[k] = v

    def drop(self):
        self._df = {}
        self.loc.df = self._df

    def query(self, k, v=None):
        if v is None:
            assert isinstance(k, dict)
            return {
                _k : self._df[_k].query(k[_k])
                for _k in k
            }
        else:
            assert k is not None and v is not None
            return self._df[k].query(v)

    def eval(self, k, v=None):
        if v is None:
            assert isinstance(k, dict)
            return {
                _k : self._df[_k].eval(k[_k])
                for _k in k
            }
        else:
            assert k is not None and v is not None
            return self._df[k].eval(v)

    def filter(self, k, v=None):
        def do(k,v):
            assert isinstance(v, str)
            assert k in self
            self._df['/filter'].loc[k]['filter'] = v
        if v is None:
            assert isinstance(k, dict)
            for k,v in k.items():
                do(k,v)
        else:
            assert k is not None and v is not None
            do(k,v)

    def get_filter(self):
        return self._df['/filter'].drop(self.__class__.PRIVATE_KEYS)

    def __getitem__(self, k, private_key=False):
        """Read Only"""
        if k[0] != '/':
            k = '/'+k
        assert private_key or k not in self.__class__.PRIVATE_KEYS
        if k not in self._df:
            raise KeyError()
        query = self._df['/filter'].loc[k]['filter']
        if query:
            return self._df[k].query(query)
        else:
            return self._df[k].copy()

    def __setitem__(self, k, v, private_key=False):
        assert isinstance(k, str)
        if k[0] != '/':
            k = '/'+k
        assert private_key or k not in self.__class__.PRIVATE_KEYS
        assert isinstance(v, pd.DataFrame)
        self._df[k] = v
        if k not in self._df.setdefault('/filter', pd.DataFrame({'filter':['']}, index=['/filter'])).index.values:
            self._df['/filter'] = self._df['/filter'].append(
                pd.DataFrame({'filter':['']},index=[k]),
                verify_integrity=True,
            )

    def __iter__(self):
        return iter(filter(lambda k : k not in self.__class__.PRIVATE_KEYS, iter(self._df)))

    def __contains__(self, v):
        return v in self._df

    def values(self):
        for k,v in self.items():
            yield v

    def items(self):
        return filter(lambda i : i[0] not in self.__class__.PRIVATE_KEYS, self._df.items())

    def keys(self):
        return filter(lambda k : k not in self.__class__.PRIVATE_KEYS, self._df.keys())

    def save(self, hdf_path):
        if os.path.splitext(hdf_path)[1] != '.h5':
            raise FileExtensionError(hdf_path, '.h5')
        if os.path.exists(hdf_path):
            logging.info('Overwriting %s' % hdf_path)
            os.remove(hdf_path)
        if len(self._df) == 0:
            logging.warn('Will not save empty DataFrameCollection')
        for k,v in self._df.items():
            logging.info('Saving %s' % k)
            v.to_hdf(hdf_path, key=k, mode='a')

    def load(self, hdf_path):
        if os.path.splitext(hdf_path)[1] != '.h5':
            raise FileExtensionError(hdf_path, '.h5')
        with pd.HDFStore(hdf_path) as store:
            logging.info('Loading %s' % hdf_path)
            self.drop()
            for k in store.keys():
                logging.info('Loading %s' % k)
                self.__setitem__(k, store[k], True)
