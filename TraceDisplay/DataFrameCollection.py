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

class MetaDataFrame(object):
    def __init__(self, dfc, df):
        assert isinstance(dfc, DataFrameCollection)
        assert not hasattr(dfc, self.__class__.ATTR)
        assert self.__class__.KEY not in dfc.private_key
        setattr(dfc, self.__class__.ATTR, self)
        dfc.private_key.append(self.__class__.KEY)
        self.dfc = dfc
        self.df = df
        self.df_at_init = df
    def __hasattr__(self, k):
        if k not in ['df']:
            return super(MetaDataFrame, self).__hasattr__(k)
        else:
            return True
    def __setattr__(self, k, v):
        if k not in ['df']:
            super(MetaDataFrame, self).__setattr__(k, v)
        else:
            assert isinstance(v, pd.DataFrame)
            self.dfc.setitem(self.__class__.KEY, v, private_key=True)
    def __getattr__(self, k):
        if k not in ['df']:
            return super(MetaDataFrame, self).__getattr__(k)
        else:
            return self.dfc.getitem(self.__class__.KEY, private_key=True, inplace=True)
    def _repr_html_(self):
        return self.df.drop(self.dfc.private_key)._repr_html_()
    def __contains__(self, k):
        return k in self.df.index
    def __getitem__(self, k):
        return self.df.loc[k]
    def __setitem__(self, k, v):
        if k not in self:
            self.df = self.df.append(
                pd.DataFrame(v, index=[k]),
                sort=True,
                verify_integrity=True,
            )
        else:
            self.df.loc[k] = v
    def get(self, k, default):
        if k not in self:
            return default
        return self[k]
    def setdefault(self, k, default):
        if k not in self:
            self[k] = default
        return self[k]
    def update(self, d):
        for k,v in d.items():
            self[k] = v
    def append(self, v):
        self[len(self.df)] = v
    def extend(self, a):
        for v in a:
            self.append(v)
    def clear(self):
        self.df = pd.DataFrame(self.df_at_init)

class FilterDataFrame(MetaDataFrame):
    ATTR = 'filter'
    KEY  = '/filter'
    def __init__(self, dfc, df=pd.DataFrame()):
        super(FilterDataFrame, self).__init__(dfc, df)
        self.dfc_override_getitem = dfc.override_getitem
        dfc.override_getitem = self.filtered_getitem
    def filtered_getitem(self, k, private_key=False, inplace=False):
        query = self[k][self.__class__.ATTR]
        if query:
            return self.dfc_override_getitem(k, private_key, inplace).query(query)
        else:
            return self.dfc_override_getitem(k, private_key, inplace)
    def __getitem__(self, k):
        assert k in self.dfc
        return self.setdefault(k, {self.__class__.ATTR:['']})
    def __setitem__(self, k, v):
        assert isinstance(v, str)
        assert k in self.dfc
        if k not in self:
            self.setdefault(k, {self.__class__.ATTR:[v]})
        else:
            super(FilterDataFrame, self).__setitem__(k, v)
    def setdefault(self, k, default):
        if k not in self:
            super(FilterDataFrame, self).__setitem__(k, default)
        return super(FilterDataFrame, self).__getitem__(k)

class DataFrameCollection(object):
    PRIVATE_KEYS = [] # TODO: rm
    def __init__(self, dict_of_data_frames={}, use_filter=True):
        self.override_getitem = self.getitem
        self.override_setitem = self.setitem
        self.private_key = self.__class__.PRIVATE_KEYS.copy()
        self._df = {}
        self.loc = Loc(self._df)
        if use_filter:
            FilterDataFrame(self)
        assert isinstance(dict_of_data_frames, dict)
        for k,v in dict_of_data_frames.items():
            self[k] = v

    def key(self, k):
        if k[0] != '/':
            k = '/'+k
        return k

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

    def __getitem__(self, k, private_key=False, inplace=False):
        return self.override_getitem(k, private_key, inplace)

    def getitem(self, k, private_key=False, inplace=False):
        """Read Only"""
        k = self.key(k)
        assert private_key or k not in self.private_key
        if k not in self._df:
            raise KeyError(k)
        if inplace:
            return self._df[k]
        else:
            return self._df[k].copy()

    def __setitem__(self, k, v, private_key=False):
        self.override_setitem(k, v, private_key)

    def setitem(self, k, v, private_key=False):
        assert isinstance(k, str)
        k = self.key(k)
        assert private_key or k not in self.private_key
        assert isinstance(v, pd.DataFrame)
        self._df[k] = v

    def __iter__(self):
        return iter(filter(lambda k : k not in self.private_key, iter(self._df)))

    def __contains__(self, k):
        k = self.key(k)
        return k in self._df

    def values(self):
        for k,v in self.items():
            yield v

    def items(self):
        return filter(lambda i : i[0] not in self.private_key, self._df.items())

    def keys(self):
        return filter(lambda k : k not in self.private_key, self._df.keys())

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
            for k in store.keys():
                logging.info('Loading %s' % k)
                self.__setitem__(k, store[k], True)
