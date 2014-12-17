#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import os
import sys
import datetime
import json
import cPickle as pickle
#import pickle
import shutil
import contextlib
import threading
import re

from threading import RLock

import data_utils
import utils

import bayesdb.settings as S


class ModelLocks():
    """
    Creates individual model-level locks.
    Any user method always needs to acquire locks in ascending order to avoid deadlock!!!!
    """

    def __init__(self, persistence_layer):
        self.tablename_dict = dict()
        self.persistence_layer = persistence_layer

        for tablename in self.persistence_layer.btable_index:
            self.tablename_dict[tablename] = dict()
            modelids = self.persistence_layer.get_model_ids(tablename)
            for modelid in modelids:
                self.tablename_dict[tablename][modelid] = RLock()

    def add_tablename_if_not_exist(self, tablename):
        if tablename not in self.tablename_dict:
            self.tablename_dict[tablename] = dict()

    def add_model_if_not_exist(self, tablename, modelid):
        if modelid not in self.tablename_dict[tablename]:
            self.tablename_dict[tablename][modelid] = RLock()

    def acquire(self, tablename, modelid):
        self.add_tablename_if_not_exist(tablename)
        self.add_model_if_not_exist(tablename, modelid)

        self.tablename_dict[tablename][modelid].acquire()

    def release(self, tablename, modelid):
        if modelid in self.tablename_dict[tablename]:
            self.tablename_dict[tablename][modelid].release()

    def acquire_table(self, tablename):
        self.add_tablename_if_not_exist(tablename)
        for modelid in sorted(self.tablename_dict[tablename].keys()):
            self.tablename_dict[tablename][modelid].acquire()

    def release_table(self, tablename):
        for modelid, lock in self.tablename_dict[tablename].items():
            # Only release locks this thread owns. There could be a case where
            # a new model was created while he had the table lock.
            if threading.current_thread().ident == lock._RLock__owner:
                lock.release()

    def drop(self, tablename, modelid):
        del self.tablename_dict[tablename][modelid]

    def drop_all(self, tablename):
        self.tablename_dict[tablename] = dict()


class PersistenceLayer(object):
    """
    Stores btables in the following format in the "data" directory:
    bayesdb/data/
    ..btable_index.pkl
    ..<tablename>/
    ....metadata_full.pkl
    ....metadata.pkl
    ....column_labels.pkl
    ....column_lists.pkl
    ....row_lists.pkl
    ....models/
    ......diagnostic_data.pkl
    ......model_<id>.pkl

    table_index.pkl: list of btable names.

    metadata.pkl: dict. keys: M_r, M_c, T, cctypes
    metadata_full.pkl: dict. keys: M_r_full, M_c_full, T_full, cctypes_full
    column_lists.pkl: dict. keys: column list names, values: list of column names.
    row_lists.pkl: dict. keys: row list names, values: list of row keys (need to update all these if
        table key is changed!).
    models.pkl: dict[model_idx] -> dict[X_L, X_D, iterations, column_crp_alpha, logscore, num_views,
        model_config]. Idx starting at 1.
    diagnostic_data.pkl: dict[model_idx] -> dict[score, num_views, min_cluster_view,
        mean_cluster_view, max_cluster_view, ...more to come] each entry of which is dict with keys
        'value' and 'step'. For example, the 'score' diagnostic for model 9 which has been
        storing diagnostic data every 5 transition steps for 10 transitions may look like:
        diagnostic_data[9]['score'] => {'value': [-1023.0246, -842.8801, -820.3913],
        'step':[0, 4, 9]}
    data.csv: the raw csv file that the data was loaded from.

    Should be a Singleton class, but Python doesn't enforce that. Could be refactored as just a
    module.
    """

    def __init__(self):
        """
        Create data directory if doesn't exist: every other function requires data_dir.
        """
        self.cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.cur_dir, 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.load_btable_index()  # sets self.btable_index
        self.model_locks = ModelLocks(self)
        self.btable_check_index = list()

    def load_btable_index(self):
        """
        Create btable_index.pkl with an empty list if it doesn't exist; otherwise, read its
        contents.
        Set it to self.btable_index
        """
        btable_index_path = os.path.join(self.data_dir, 'btable_index.pkl')
        if not os.path.exists(btable_index_path):
            self.btable_index = []
            self.write_btable_index()
        else:
            f = open(btable_index_path, 'rb')
            self.btable_index = pickle.load(f)
            f.close()

    def write_btable_index(self):
        btable_index_path = os.path.join(self.data_dir, 'btable_index.pkl')
        f = open(btable_index_path, 'wb')
        pickle.dump(self.btable_index, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def add_btable_to_index(self, tablename):
        self.btable_index.append(tablename)
        self.write_btable_index()

    def remove_btable_from_index(self, tablename):
        self.btable_index.remove(tablename)
        self.write_btable_index()

    def get_metadata(self, tablename):
        try:
            x = os.path.join(self.data_dir, tablename, 'metadata.pkl')
            f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'rb')
        except Exception as e:
            raise utils.BayesDBError("Error: metadata does not exist. Has %s been corrupted?"
                                     % self.data_dir)
        try:
            metadata = pickle.load(f)
        except Exception as e:
            raise utils.BayesDBError("Error: metadata file could not be loaded for table %s"
                                     % tablename)
        f.close()
        return metadata

    def get_metadata_full(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'rb')
        except Exception as e:
            raise utils.BayesDBError("Error: metadata_full file doesn't exist. This is most "
                                     "likely a result of this btable being created with an old "
                                     "version of BayesDB. Please try recreating the table from "
                                     "the original csv, and loading any models you might have.")
        metadata = pickle.load(f)
        f.close()
        return metadata

    def write_metadata(self, tablename, metadata):
        metadata_f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'wb')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        metadata_f.close()

    def write_metadata_full(self, tablename, metadata):
        metadata_f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'wb')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        metadata_f.close()

    def drop_column_list(self, tablename, list_name):
        column_lists = self.get_column_lists(tablename)
        if list_name in column_lists:
            column_lists.pop(list_name, None)
        elif '%s_0' % list_name in column_lists:
            suffix = 0
            while '%s_%d' % (list_name, suffix) in column_lists:
                column_lists.pop('%s_%d' % (list_name, suffix), None)
                suffix += 1
        else:
            raise utils.BayesDBColumnListDoesNotExistError(list_name, tablename)
        self.write_column_lists(tablename, column_lists)

    def drop_row_list(self, tablename, list_name):
        row_lists = self.get_row_lists(tablename)
        if list_name in row_lists:
            row_lists.pop(list_name, None)
        elif '%s_0' % list_name in row_lists:
            suffix = 0
            while '%s_%d' % (list_name, suffix) in row_lists:
                row_lists.pop('%s_%d' % (list_name, suffix), None)
                suffix += 1
        else:
            raise utils.BayesDBRowListDoesNotExistError(list_name, tablename)
        self.write_row_lists(tablename, row_lists)

    def get_model_config(self, tablename):
        """
        Just loads one model, and gets the model_config from it.
        """
        model = self.get_models(tablename, modelid=self.get_max_model_id(tablename))
        if model is None:
            return None
        if 'model_config' in model:
            return model['model_config']
        else:
            return None

    def get_models(self, tablename, modelid=None):
        """
        Return the models dict for the table if modelid is None.
        If modelid is an int, then return the model specified by that id.
        If modelid is a list, then get each individual model specified by each int in that list.
        """
        models_dir = os.path.join(self.data_dir, tablename, 'models')
        if os.path.exists(models_dir):
            if modelid is not None:
                def get_single_model(modelid):
                    self.model_locks.acquire(tablename, modelid)
                    # Only return one of the models
                    full_fname = os.path.join(models_dir, 'model_%d.pkl' % modelid)
                    if not os.path.exists(full_fname):
                        self.model_locks.release(tablename, modelid)
                        return None
                    f = open(full_fname, 'rb')
                    m = pickle.load(f)
                    f.close()
                    self.model_locks.release(tablename, modelid)
                    return m
                if type(modelid) == list:
                    models = {}
                    for i in modelid:
                        if not utils.is_int(i):
                            raise utils.BayesDBError('Invalid modelid: %s' % str(modelid))
                        models[i] = get_single_model(int(i))
                    return models
                elif utils.is_int(modelid):
                    return get_single_model(int(modelid))
                else:
                    raise utils.BayesDBError('Invalid modelid: %s' % str(modelid))
            else:
                # Return all the models
                models = {}
                self.model_locks.acquire_table(tablename)
                fnames = os.listdir(models_dir)
                for fname in fnames:
                    if fname.startswith('model_'):
                        model_id = fname[6:]  # remove preceding 'model_'
                        model_id = int(model_id[:-4])  # remove trailing '.pkl' and cast to int
                        full_fname = os.path.join(models_dir, fname)
                        f = open(full_fname, 'rb')
                        m = pickle.load(f)
                        f.close()
                        models[model_id] = m
                self.model_locks.release_table(tablename)
                return models
        else:
            # Backwards compatibility with old model style.
            self.model_locks.acquire_table(tablename)
            try:
                f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'rb')
                models = pickle.load(f)
                f.close()
                if modelid is not None:
                    ret = models[modelid]
                else:
                    ret = models
                self.model_locks.release_table(tablename)
                return ret
            except IOError:
                self.model_locks.release_table(tablename)
                return {}

    def get_column_labels(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'column_labels.pkl'), 'rb')
            column_labels = pickle.load(f)
            f.close()
            return column_labels
        except IOError:
            return dict()

    def get_column_lists(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'rb')
            column_lists = pickle.load(f)
            f.close()
            return column_lists
        except IOError:
            return dict()

    def get_row_lists(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'row_lists.pkl'), 'rb')
            row_lists = pickle.load(f)
            f.close()
            return row_lists
        except IOError:
            return dict()

    def column_list_exists(self, tablename, list_name):
        '''
        Return True if list_name or list_name_0 exist as column lists.
        '''
        column_lists = self.get_column_lists(tablename)
        result = list_name in column_lists or '%s_0' % list_name in column_lists
        return result

    def row_list_exists(self, tablename, list_name):
        '''
        Return True if list_name or list_name_0 exist as column lists.
        '''
        row_lists = self.get_row_lists(tablename)
        result = list_name in row_lists or '%s_0' % list_name in row_lists
        return result

    def get_user_metadata(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'user_metadata.pkl'), 'rb')
            column_labels = pickle.load(f)
            f.close()
            return column_labels
        except IOError:
            return dict()

    def add_user_metadata(self, tablename, metadata_key, metadata_value):
        user_metadata = self.get_user_metadata(tablename)
        user_metadata[metadata_key.lower()] = metadata_value
        self.write_user_metadata(tablename, user_metadata)

    def add_column_label(self, tablename, column_name, column_label):
        column_labels = self.get_column_labels(tablename)
        column_labels[column_name.lower()] = column_label
        self.write_column_labels(tablename, column_labels)

    def add_column_list(self, tablename, column_list_name, column_list):
        column_lists = self.get_column_lists(tablename)
        column_lists[column_list_name] = column_list
        self.write_column_lists(tablename, column_lists)

    def add_row_list(self, tablename, row_list_name, row_list):
        row_lists = self.get_row_lists(tablename)
        row_lists[row_list_name] = row_list
        self.write_row_lists(tablename, row_lists)

    def get_column_label(self, tablename, column_name):
        column_labels = self.get_column_labels(tablename)
        if column_name.lower() in column_labels:
            return column_labels[column_name.lower()]
        else:
            raise utils.BayesDBError('Column %s in btable %s has no label.'
                                     % (column_name, tablename))

    def get_column_list(self, tablename, column_list):
        column_lists = self.get_column_lists(tablename)
        if column_list in column_lists:
            return column_lists[column_list]
        else:
            raise utils.BayesDBColumnListDoesNotExistError(column_list, tablename)

    def get_row_list(self, tablename, row_list):
        row_lists = self.get_row_lists(tablename)
        if row_list in row_lists:
            return row_lists[row_list]
        else:
            raise utils.BayesDBRowListDoesNotExistError(row_list, tablename)

    def write_model(self, tablename, model, modelid):
        # Make models dir
        models_dir = os.path.join(self.data_dir, tablename, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        self.model_locks.acquire(tablename, modelid)
        model_f = open(os.path.join(models_dir, 'model_%d.pkl' % modelid), 'wb')
        pickle.dump(model, model_f, pickle.HIGHEST_PROTOCOL)
        model_f.close()
        self.model_locks.release(tablename, modelid)

    def write_models(self, tablename, models):
        # Make models dir
        models_dir = os.path.join(self.data_dir, tablename, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        # Write each model individually
        for i, v in models.items():
            self.model_locks.acquire(tablename, modelid)
            model_f = open(os.path.join(models_dir, 'model_%d.pkl' % i), 'wb')
            pickle.dump(v, model_f, pickle.HIGHEST_PROTOCOL)
            model_f.close()
            self.model_locks.release(tablename, modelid)

    def write_column_labels(self, tablename, column_labels):
        column_labels_f = open(os.path.join(self.data_dir, tablename, 'column_labels.pkl'), 'wb')
        pickle.dump(column_labels, column_labels_f, pickle.HIGHEST_PROTOCOL)
        column_labels_f.close()

    def write_user_metadata(self, tablename, user_metadata):
        user_metadata_f = open(os.path.join(self.data_dir, tablename, 'user_metadata.pkl'), 'wb')
        pickle.dump(user_metadata, user_metadata_f, pickle.HIGHEST_PROTOCOL)
        user_metadata_f.close()

    def write_column_lists(self, tablename, column_lists):
        column_lists_f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'wb')
        pickle.dump(column_lists, column_lists_f, pickle.HIGHEST_PROTOCOL)
        column_lists_f.close()

    def write_row_lists(self, tablename, row_lists):
        row_lists_f = open(os.path.join(self.data_dir, tablename, 'row_lists.pkl'), 'wb')
        pickle.dump(row_lists, row_lists_f, pickle.HIGHEST_PROTOCOL)
        row_lists_f.close()

    def drop_btable(self, tablename):
        """Delete a single btable."""
        if tablename in self.btable_index:
            path = os.path.join(self.data_dir, tablename)
            if os.path.isdir(path):
                shutil.rmtree(path)
            self.remove_btable_from_index(tablename)
        return 0

    def list_btables(self):
        """Return a list of all btable names."""
        return self.btable_index

    def drop_models(self, tablename, model_ids='all'):
        """ Delete a single model, or all, if model_ids == 'all' or None. """
        models_dir = os.path.join(self.data_dir, tablename, 'models')
        if os.path.exists(models_dir):
            if model_ids is None or model_ids == 'all':
                self.model_locks.acquire_table(tablename)
                fnames = os.listdir(models_dir)
                for fname in fnames:
                    if 'model_' in fname:
                        os.remove(os.path.join(models_dir, fname))
                self.model_locks.drop_all(tablename)
                self.model_locks.release_table(tablename)
            else:
                for modelid in model_ids:
                    self.model_locks.acquire(tablename, modelid)
                    fname = os.path.join(models_dir, 'model_%d.pkl' % modelid)
                    if os.path.exists(fname):
                        os.remove(fname)
                    self.model_locks.drop(tablename, modelid)
                    self.model_locks.release(tablename, modelid)
        else:
            # If models in old style, convert to new style, save, and retry.
            models = self.get_models(tablename)
            self.write_models(tablename, models)
            self.drop_models(tablename, model_ids)

    def get_latent_states(self, tablename, modelid=None):
        """Return X_L_list, X_D_list, and M_c"""
        metadata = self.get_metadata(tablename)
        models = self.get_models(tablename, modelid)
        if None in models.values():
            raise utils.BayesDBError('Invalid model id. Use "SHOW MODELS FOR <btable>" to see '
                                     'valid model ids.')
        M_c = metadata['M_c']
        X_L_list = [model['X_L'] for model in models.values()]
        X_D_list = [model['X_D'] for model in models.values()]
        return (X_L_list, X_D_list, M_c)

    def get_metadata_and_table(self, tablename):
        """Return M_c and M_r and T"""
        metadata = self.get_metadata(tablename)
        M_c = metadata['M_c']
        M_r = metadata['M_r']
        T = metadata['T']
        return M_c, M_r, T

    def get_metadata_and_table_full(self, tablename):
        """Return M_c_full and M_r_full and T_full"""
        metadata_full = self.get_metadata_full(tablename)
        M_c_full = metadata_full['M_c_full']
        M_r_full = metadata_full['M_r_full']
        T_full = metadata_full['T_full']
        return M_c_full, M_r_full, T_full

    def has_models(self, tablename):
        return self.get_max_model_id(tablename) != -1

    def get_max_model_id(self, tablename, models=None):
        """Get the highest model id, and -1 if there are no models.
        Model indexing starts at 0 when models exist."""
        model_ids = self.get_model_ids(tablename, models)
        if len(model_ids) == 0:
            return -1
        else:
            return max(model_ids)

    def get_model_ids(self, tablename, models=None):
        """Get the list of modelids for a table."""
        if models is not None:
            model_ids = models.keys()
        else:
            models_dir = os.path.join(self.data_dir, tablename, 'models')
            if not os.path.exists(models_dir):
                model_ids = []
            else:
                model_ids = []
                fnames = os.listdir(models_dir)
                for fname in fnames:
                    if fname.startswith('model_'):
                        model_id = fname[6:]  # remove preceding 'model_'
                        model_id = int(model_id[:-4])  # remove trailing '.pkl' and cast to int
                        model_ids.append(model_id)
        return model_ids

    def get_cctypes(self, tablename):
        """Access the table's current cctypes."""
        metadata = self.get_metadata(tablename)
        return metadata['cctypes']

    def get_cctypes_full(self, tablename):
        """Access the table's current cctypes."""
        metadata_full = self.get_metadata_full(tablename)
        return metadata_full['cctypes_full']

    def get_colnames(self, tablename):
        """
        Return column names of analysis columns
        """
        M_c = self.get_metadata(tablename)['M_c']
        colnames = utils.get_all_column_names_in_original_order(M_c)
        return colnames

    def get_colnames_full(self, tablename):
        """
        Return column names of all columns
        """
        M_c_full = self.get_metadata_full(tablename)['M_c_full']
        colnames = utils.get_all_column_names_in_original_order(M_c_full)
        return colnames

    def get_schema(self, tablename):
        """
        Return colnames and cctypes of analysis columns
        """
        colnames = self.get_colnames(tablename)
        cctypes = self.get_cctypes(tablename)
        M_c = self.get_metadata(tablename)['M_c']
        schema = dict()
        for colname, cctype in zip(colnames, cctypes):
            schema[colname] = dict()
            schema[colname]['cctype'] = cctype
            if cctype == 'cyclic':
                col_idx = M_c['name_to_idx'][colname]
                schema[colname]['parameters'] = M_c['column_metadata'][col_idx]['parameters']
            else:
                schema[colname]['parameters'] = None
        return schema

    def get_schema_full(self, tablename):
        """
        Return colnames and cctypes of all columns
        """
        colnames_full = self.get_colnames_full(tablename)
        cctypes_full = self.get_cctypes_full(tablename)
        schema_full = dict()
        for colname, cctype in zip(colnames_full, cctypes_full):
            schema_full[colname] = cctype
        return schema_full

    def get_key_column_name(self, tablename):
        metadata_full = self.get_metadata_full(tablename)
        try:
            key_column_index = metadata_full['cctypes_full'].index('key')
        except ValueError as e:
            print("If your btable was created with an older version of BayesDB, it might not have "
                  "a default key column.")
            key_column_index = metadata_full['cctypes_full'].index('key')
        key_column_name = metadata_full['M_c_full']['idx_to_name'][str(key_column_index)]
        return key_column_name

    def update_metadata(self, tablename, M_r=None, M_c=None, T=None, cctypes=None):
        """Overwrite M_r, M_c, and T (not cctypes) for the table."""
        metadata = self.get_metadata(tablename)
        if M_r:
            metadata['M_r'] = M_r
        if M_c:
            metadata['M_c'] = M_c
        if T:
            metadata['T'] = T
        if cctypes:
            metadata['cctypes'] = cctypes
        f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'wb')
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def update_metadata_full(self, tablename, M_r_full=None, M_c_full=None, T_full=None,
                             cctypes_full=None):
        """Overwrite M_r, M_c, and T (not cctypes) for the table."""
        metadata = self.get_metadata_full(tablename)
        if M_r_full:
            metadata['M_r_full'] = M_r_full
        if M_c_full:
            metadata['M_c_full'] = M_c_full
        if T_full:
            metadata['T_full'] = T_full
        if cctypes_full:
            metadata['cctypes_full'] = cctypes_full
        f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'wb')
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def gen_default_codebook(self, M_c_full):
        """ Generates default metadata.

        Args:
            M_c_full (dict): M_c_full metadata object

        Returns:
            list of dict: num_cols length codebook, where each entry is a dict with keys:
                short_name, description, and valuemap with defaults colname, 'No description', and
                None, repsectively.
        """
        if 'column_codebook' in M_c_full:
            empty_codebook_entires = False
            for entry in M_c_full['column_codebook']:
                if entry is None:
                    empty_codebook_entires = True
                    break
            if not empty_codebook_entires:
                return

        column_codebook = [None]*len(M_c_full['name_to_idx'])

        for colname, idx in M_c_full['name_to_idx'].iteritems():
            column_codebook[idx] = {
                'description': 'No description.',
                'short_name': colname,
                'value_map': None
            }

        return column_codebook

    def update_codebook(self, tablename, codebook):
        """ Adds a codebook to a btable from a .csv

        Args:
            tablename (str): Name of the btable
            codebook (list of dict): The processed codebook. Should come from client because we
                assume that .csv is stored on the client machine.
        """
        # metadata_full = self.get_metadata_full(tablename)
        # M_c_full = metadata_full['M_c_full']
        #
        # if isinstance(codebook, dict):
        #     name_to_idx = M_c_full['name_to_idx']
        #     column_codebook = [None]*len(name_to_idx)
        #     for colname, idx in name_to_idx.iteritems():
        #         if colname in codebook.keys():
        #             column_codebook[idx] = codebook[colname]
        #     M_c_full['column_codebook'] = column_codebook
        #
        # elif isinstance(codebook, list):
        #     if not isinstance(codebook[0], dict):
        #         raise TypeError("Error: Invalid codebook.")
        #     M_c_full['column_codebook'] = codebook
        #
        # self.update_metadata_full(tablename, M_c_full=M_c_full)

        # Bax: I'm killing this feature (maybe temporarily) because there would be problems with
        # model metadata if value maps are updated. If no models have been created and there is a
        # codebook in place, it is trival for the user to create a new btable.
        raise NotImplementedError('UPDATE CODEBOOK is not currently implemented.\n Updating value '
                                  'Please recreate your BTABLE')

    def add_default_codebook_to_metadata(self, tablename):
        """ Adds the default metadata to tablename"""
        metadata_full = self.get_metadata_full(tablename)
        column_codebook = self.gen_default_codebook(metadata_full['M_c_full'])
        self.update_codebook_from_csv(tablename, column_codebook)

    def check_if_table_exists(self, tablename):
        """Return true iff this tablename exists in the persistence layer."""
        return tablename in self.btable_index

    def update_schema(self, tablename, mappings):
        """
        mappings is a dict of column name to 'cyclic', 'numerical', 'categorical', 'ignore', or
        'key'.
        TODO: can we get rid of cctypes?
        """
        metadata_full = self.get_metadata_full(tablename)
        cctypes_full = metadata_full['cctypes_full']
        M_c_full = metadata_full['M_c_full']
        raw_T_full = metadata_full['raw_T_full']
        colnames_full = utils.get_all_column_names_in_original_order(M_c_full)
        try:
            parameters_full = [x['parameters'] for x in M_c_full['column_metadata']]
        except KeyError:
            print('WARNING: resetting parameters to defaults. Please check these values with '
                  'DESCRIBE and adjust them manually if necessary.')
            parameters_full = []
            for md in M_c_full['column_metadata']:
                if 'dirichlet' in md['modeltype']:
                    params = {
                        'cardinality': len(md['value_to_code'])
                    }
                elif'vonmises' in md['modeltype']:
                    params = {
                        'min': 0.0,
                        'max': 2.0*3.14159265358979323846264338328
                    }
                else:
                    params = None

                parameters_full.append(params)

            parameters_full = [None for _ in range(len(M_c_full['column_metadata']))]

        # Now, update cctypes_full (cctypes updated later, after removing ignores).
        mapping_set = 'numerical', 'categorical', 'ignore', 'key', 'cyclic'

        for colname, mapping in mappings.items():
            cctype = mapping['cctype']
            parameters = mapping['parameters']

            if colname.lower() not in M_c_full['name_to_idx']:
                raise utils.BayesDBError('Error: column %s does not exist.' % colname)
            elif cctype not in mapping_set:
                raise utils.BayesDBError('Error: datatype %s is not one of the valid datatypes: %s.'
                                         % (mapping, str(mapping_set)))

            cidx = M_c_full['name_to_idx'][colname.lower()]

            # If the column's current type is key, don't allow the change.
            if cctypes_full[cidx] == 'key':
                raise utils.BayesDBError('Error: %s is already set as the table key. To change its '
                                         'type, reload the table using CREATE BTABLE and choose a '
                                         'different key column.' % colname.lower())
            # If the user tries to change a column to key, it's easier to reload the table, since at
            # this point there aren't models anyways. Eventually we can build this in if it's
            # desirable.
            elif cctype == 'key':
                raise utils.BayesDBError('Error: key column already exists. To choose a different '
                                         'key, reload the table using CREATE BTABLE')

            cctypes_full[cidx] = cctype
            parameters_full[cidx] = parameters

        # Make sure there isn't more than one key.
        assert len(filter(lambda x: x == 'key', cctypes_full)) == 1

        T_full, M_r_full, M_c_full, _ = data_utils.gen_T_and_metadata(colnames_full, raw_T_full,
                                                                      cctypes=cctypes_full,
                                                                      parameters=parameters_full)

        # Variables without "_full" don't include ignored columns.
        raw_T, cctypes, colnames, parameters = data_utils.remove_ignore_cols(raw_T_full,
                                                                             cctypes_full,
                                                                             colnames_full,
                                                                             parameters_full)
        T, M_r, M_c, _ = data_utils.gen_T_and_metadata(colnames, raw_T, cctypes=cctypes,
                                                       parameters=parameters)

        # Now, put cctypes, T, M_c, and M_r back into the DB
        self.update_metadata(tablename, M_r, M_c, T, cctypes)
        self.update_metadata_full(tablename, M_r_full, M_c_full, T_full, cctypes_full)

        return self.get_metadata_full(tablename)

    def create_btable(self, tablename, cctypes_full, cctypes, T, M_r, M_c, T_full, M_r_full,
                      M_c_full, raw_T_full, T_sub=None):
        """
        This function is called to create a btable.
        It creates the table's persistence directory, saves data.csv and metadata.pkl.
        Creates models.pkl as empty dict.

        """
        # Make directory for table
        if not os.path.exists(os.path.join(self.data_dir, tablename)):
            os.mkdir(os.path.join(self.data_dir, tablename))

        # Write metadata and metadata_full
        metadata_full = dict(M_c_full=M_c_full, M_r_full=M_r_full, T_full=T_full,
                             cctypes_full=cctypes_full, raw_T_full=raw_T_full)
        self.write_metadata_full(tablename, metadata_full)
        metadata = dict(M_c=M_c, M_r=M_r, T=T, cctypes=cctypes, T_sub=T_sub)
        self.write_metadata(tablename, metadata)

        # Write models
        models = {}
        self.write_models(tablename, models)

        # Write column labels
        column_labels = dict()
        self.write_column_labels(tablename, column_labels)

        # Write column lists
        column_lists = dict()
        self.write_column_lists(tablename, column_lists)

        # Write row lists
        row_lists = dict()
        self.write_row_lists(tablename, row_lists)

        # Add to btable name index
        self.add_btable_to_index(tablename)

    def upgrade_btable(self, tablename, cctypes_full, T_full, M_r_full, M_c_full, raw_T_full):
        """
        This function is called to upgrade a btable.
        Right now, it only updates the _full version of variables, because those are the only
        possible upgraded attributes, because the only possible upgrade reasons are:
        1. Creation of metadata_full
        2. Addition of key column.

        This will leave models, column labels, columns lists, and row lists intact.
        """
        # Write metadata_full
        metadata_full = dict(M_c_full=M_c_full, M_r_full=M_r_full, T_full=T_full,
                             cctypes_full=cctypes_full, raw_T_full=raw_T_full)
        self.write_metadata_full(tablename, metadata_full)

    def add_models(self, tablename, model_list):
        """
        Add a set of models (X_Ls and X_Ds) to a table (the table does not need to
        already have models).

        parameter model_list is a list of dicts, where each dict contains the keys
        X_L, X_D, and iterations.
        """
        # Model indexing starts at 0 (and is -1 if none exist)
        max_model_id = self.get_max_model_id(tablename)
        for i, m in enumerate(model_list):
            modelid = max_model_id + 1 + i
            self.write_model(tablename, m, modelid)

    def update_models(self, tablename, modelids, X_L_list, X_D_list, diagnostics_data_list,
                      increment_iterations_list=None, increment_time_list=None):
        """
        TODO: UNUSED WITH NEW ANALYZE, DELETE

        Overwrite all models by id, and append diagnostic info.

        Args:
            tablename (type): Btable name.
            X_L_list (list): List of crosscat X_L metadata from intialize or analyze
            X_D (list): List of Crosscat X_D metadata from intialize or analyze
            diagnostics_data (list of dict): List of diagnostics dict. Keys vary depending on
                tests avalible indiagnostics_utils. Each key holds only a single value.
            modelids (list of in): List of model indices.
            increment_iterations_list (list int): Number of analyze iterations since last update
                for each model.
            increment_time_list (list of float): Time (seconds) spent analyzing since last update
                for each model.
        """

        for idx, modelid in enumerate(modelids):
            if increment_iterations_list is not None:
                increment_iterations = increment_iterations[idx]
                increment_time = increment_time[idx]
            else:
                increment_iterations = 0
                increment_time = 0
            self.update_model(tablename, X_L_list[idx], X_D_list[idx], diagnostics_data_list[idx],
                              modelid, increment_iterations, increment_time)

    def update_model(self, tablename, X_L, X_D, diagnostics_data, modelid,
                     increment_iterations=0, increment_time=0):
        """ Overwrite a certain model by id.

        Overwrites current metadata and updates, trials, time, and diagnostics (if applicable).

        Args:
            tablename (type): Btable name.
            X_L (dict): Crosscat X_L metadata from intialize or analyze
            X_D (list of list of int): Crosscat X_D metadata from intialize or analyze
            diagnostics_data (dict): Diagnostics dict. Keys vary depending on tests avalible in
                diagnostics_utils. Each key holds only a single value.
            modelid (int): Model index.
            increment_iterations (int): Number of analyze iterations since last update.
            increment_time (float): Time (seconds) spent analyzing since last update.
        """
        assert type(modelid) == int
        self.model_locks.acquire(tablename, modelid)
        model = self.get_models(tablename, modelid)

        model['X_L'] = X_L
        model['X_D'] = X_D
        model['time'] = model.get('time') or 0

        if increment_iterations > 0:  # If any iterations were performed
            model['iterations'] += increment_iterations
            model['time'] += increment_time

            diagnostics_data['time'] = model['time']
            diagnostics_data['iterations'] = model['iterations']

            if 'diagnostics' not in model.keys():
                model['diagnostics'] = dict()
                for key, value in diagnostics_data.iteritems():
                    model['diagnostics'][key] = [value]
                model['diagnostics']['iterations'] = [0]
                model['diagnostics']['time'] = [0.0]
            else:
                # don't append diagnostics if this is the same timepoint
                if model['diagnostics']['iterations'][-1] != diagnostics_data['iterations'] and \
                        model['diagnostics']['time'][-1] != diagnostics_data['time']:
                    for key, value in diagnostics_data.iteritems():
                        if key not in model['diagnostics'].keys():
                            model['diagnostics'][key] = [value]
                        else:
                            model['diagnostics'][key].append(value)

        self.write_model(tablename, model, modelid)
        self.model_locks.release(tablename, modelid)
