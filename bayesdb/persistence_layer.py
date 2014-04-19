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
import pickle
import shutil
import contextlib

import data_utils
import utils

import bayesdb.settings as S


class PersistenceLayer():
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
    ......model_<id>.pkl

    table_index.pkl: list of btable names.
    
    metadata.pkl: dict. keys: M_r, M_c, T, cctypes
    metadata_full.pkl: dict. keys: M_r_full, M_c_full, T_full, cctypes_full
    column_lists.pkl: dict. keys: column list names, values: list of column names.
    row_lists.pkl: dict. keys: row list names, values: list of row keys (need to update all these if table key is changed!).
    models.pkl: dict[model_idx] -> dict[X_L, X_D, iterations, column_crp_alpha, logscore, num_views, model_config]. Idx starting at 1.
    data.csv: the raw csv file that the data was loaded from.
    """
    
    def __init__(self):
        """
        Create data directory if doesn't exist: every other function requires data_dir.
        """
        self.cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.cur_dir, 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.load_btable_index() # sets self.btable_index

    def load_btable_index(self):
        """
        Create btable_index.pkl with an empty list if it doesn't exist; otherwise, read its contents.
        Set it to self.btable_index
        """
        btable_index_path = os.path.join(self.data_dir, 'btable_index.pkl')
        if not os.path.exists(btable_index_path):
            self.btable_index = []
            self.write_btable_index()
        else:
            f = open(btable_index_path, 'r')
            self.btable_index = pickle.load(f)
            f.close()

    def write_btable_index(self):
        btable_index_path = os.path.join(self.data_dir, 'btable_index.pkl')        
        f = open(btable_index_path, 'w')
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
            f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'r')
        except Exception as e:
            raise utils.BayesDBError("Error: metadata does not exist. Has %s been corrupted?" % self.data_dir)
        metadata = pickle.load(f)
        f.close()
        return metadata

    def get_metadata_full(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'r')
        except Exception as e:
            raise utils.BayesDBError("Error: metadata_full file doesn't exist. This is most likely a result of this btable being created with an old version of BayesDB. Please try recreating the table from the original csv, and loading any models you might have.")
        metadata = pickle.load(f)
        f.close()
        return metadata

    def write_metadata(self, tablename, metadata):
        metadata_f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'w')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        metadata_f.close()

    def write_metadata_full(self, tablename, metadata):
        metadata_f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'w')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        metadata_f.close()

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
                    # Only return one of the models
                    full_fname = os.path.join(models_dir, 'model_%d.pkl' % modelid)
                    if not os.path.exists(full_fname):
                        return None
                    f = open(full_fname, 'r')
                    m = pickle.load(f)
                    f.close()
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
                fnames = os.listdir(models_dir)
                for fname in fnames:
                    model_id = fname[6:] # remove preceding 'model_'
                    model_id = int(model_id[:-4]) # remove trailing '.pkl' and cast to int
                    full_fname = os.path.join(models_dir, fname)
                    f = open(full_fname, 'r')
                    m = pickle.load(f)
                    f.close()
                    models[model_id] = m
                return models
        else:
            # Backwards compatibility with old model style.
            try:
                f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'r')
                models = pickle.load(f)
                f.close()
                if modelid is not None:
                    return models[modelid]
                else:
                    return models
            except IOError:
                return {}

    def get_column_labels(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'column_labels.pkl'), 'r')
            column_labels = pickle.load(f)
            f.close()
            return column_labels
        except IOError:
            return dict()

    def get_column_lists(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'r')
            column_lists = pickle.load(f)
            f.close()
            return column_lists
        except IOError:
            return dict()

    def get_row_lists(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'row_lists.pkl'), 'r')
            row_lists = pickle.load(f)
            f.close()
            return row_lists
        except IOError:
            return dict()

    def get_user_metadata(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'user_metadata.pkl'), 'r')
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
            raise utils.BayesDBError('Column %s in btable %s has no label.' % (column_name, tablename))
        
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

        model_f = open(os.path.join(models_dir, 'model_%d.pkl' % modelid), 'w')
        pickle.dump(model, model_f, pickle.HIGHEST_PROTOCOL)
        model_f.close()

    def write_models(self, tablename, models):
        # Make models dir
        models_dir = os.path.join(self.data_dir, tablename, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        # Write each model individually
        for i, v in models.items():
            model_f = open(os.path.join(models_dir, 'model_%d.pkl' % i), 'w')
            pickle.dump(v, model_f, pickle.HIGHEST_PROTOCOL)
            model_f.close()

    def write_column_labels(self, tablename, column_labels):
        column_labels_f = open(os.path.join(self.data_dir, tablename, 'column_labels.pkl'), 'w')
        pickle.dump(column_labels, column_labels_f, pickle.HIGHEST_PROTOCOL)
        column_labels_f.close()

    def write_user_metadata(self, tablename, user_metadata):
        user_metadata_f = open(os.path.join(self.data_dir, tablename, 'user_metadata.pkl'), 'w')
        pickle.dump(user_metadata, user_metadata_f, pickle.HIGHEST_PROTOCOL)
        user_metadata_f.close()

    def write_column_lists(self, tablename, column_lists):
        column_lists_f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'w')
        pickle.dump(column_lists, column_lists_f, pickle.HIGHEST_PROTOCOL)
        column_lists_f.close()

    def write_row_lists(self, tablename, row_lists):
        row_lists_f = open(os.path.join(self.data_dir, tablename, 'row_lists.pkl'), 'w')
        pickle.dump(row_lists, row_lists_f, pickle.HIGHEST_PROTOCOL)
        row_lists_f.close()
        
    def drop_btable(self, tablename):
        """Delete a single btable."""
        if tablename in self.btable_index:
            shutil.rmtree(os.path.join(self.data_dir, tablename))
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
                fnames = os.listdir(models_dir)
                for fname in fnames:
                    if 'model_' in fname:
                        os.remove(os.path.join(models_dir, fname))
            else:
                for modelid in model_ids:
                    fname = os.path.join(models_dir, 'model_%d.pkl' % modelid)
                    if os.path.exists(fname):
                        os.remove(fname)
        else:
            # If models in old style, convert to new style, save, and retry.
            models = self.get_models(tablename)
            self.write_models(tablename, models)
            self.drop_models(tablename, model_ids)

            
    def get_latent_states(self, tablename, modelid=None):
        """Return X_L_list, X_D_list, and M_c"""
        metadata = self.get_metadata(tablename)
        models = self.get_models(tablename, modelid)
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

    def has_models(self, tablename):
        return self.get_max_model_id(tablename) != -1

    def get_max_model_id(self, tablename, models=None):
        """Get the highest model id, and -1 if there are no models.
        Model indexing starts at 0 when models exist."""
        
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
                    model_id = fname[6:] # remove preceding 'model_'
                    model_id = int(model_id[:-4]) # remove trailing '.pkl' and cast to int
                    model_ids.append(model_id)
        if len(model_ids) == 0:
            return -1
        else:
            return max(model_ids)

    def get_cctypes(self, tablename):
        """Access the table's current cctypes."""
        metadata = self.get_metadata(tablename)
        return metadata['cctypes']


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
        f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'w')            
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def update_metadata_full(self, tablename, M_r_full=None, M_c_full=None, T_full=None, cctypes_full=None):
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
        f = open(os.path.join(self.data_dir, tablename, 'metadata_full.pkl'), 'w')            
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)
        f.close()
        

    def check_if_table_exists(self, tablename):
        """Return true iff this tablename exists in the persistence layer."""
        return tablename in self.btable_index

    def update_schema(self, tablename, mappings):
        """
        mappings is a dict of column name to 'continuous', 'multinomial', 'ignore', or 'key'.
        TODO: can we get rid of cctypes?
        """
        metadata_full = self.get_metadata_full(tablename)
        cctypes_full = metadata_full['cctypes_full']
        M_c_full = metadata_full['M_c_full']
        raw_T_full = metadata_full['raw_T_full']
        colnames_full = utils.get_all_column_names_in_original_order(M_c_full)

        # Now, update cctypes_full (cctypes updated later, after removing ignores).
        mapping_set = 'continuous', 'multinomial', 'ignore', 'key'
        for col, mapping in mappings.items():
            if col.lower() not in M_c_full['name_to_idx']:
                raise utils.BayesDBError('Error: column %s does not exist.' % col)
            if mapping not in mapping_set:
                raise utils.BayesDBError('Error: datatype %s is not one of the valid datatypes: %s.' % (mapping, str(mapping_set)))
                
            cidx = M_c_full['name_to_idx'][col.lower()]
            cctypes_full[cidx] = mapping

        assert len(filter(lambda x: x=='key', cctypes_full)) <= 1

        if cctypes_full is None:
            cctypes_full = data_utils.guess_column_types(raw_T_full)
        T_full, M_r_full, M_c_full, _ = data_utils.gen_T_and_metadata(colnames_full, raw_T_full, cctypes=cctypes_full)

        # variables without "_full" don't include ignored columns.
        raw_T, cctypes, colnames = data_utils.remove_ignore_cols(raw_T_full, cctypes_full, colnames_full)
        T, M_r, M_c, _ = data_utils.gen_T_and_metadata(colnames, raw_T, cctypes=cctypes)
          

        # Now, put cctypes, T, M_c, and M_r back into the DB
        self.update_metadata(tablename, M_r, M_c, T, cctypes)
        self.update_metadata_full(tablename, M_r_full, M_c_full, T_full, cctypes_full)
        
        return self.get_metadata_full(tablename)
        

    def create_btable(self, tablename, cctypes_full, T, M_r, M_c, T_full, M_r_full, M_c_full, raw_T_full):
        """
        This function is called to create a btable.
        It creates the table's persistence directory, saves data.csv and metadata.pkl.
        Creates models.pkl as empty dict.
        """
        # Make directory for table
        if not os.path.exists(os.path.join(self.data_dir, tablename)):
            os.mkdir(os.path.join(self.data_dir, tablename))        

        # Write metadata and metadata_full
        metadata_full = dict(M_c_full=M_c_full, M_r_full=M_r_full, T_full=T_full, cctypes_full=cctypes_full, raw_T_full=raw_T_full)
        self.write_metadata_full(tablename, metadata_full)
        metadata = dict(M_c=M_c, M_r= M_r, T=T, cctypes=cctypes_full)
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


    def add_models(self, tablename, model_list):
        """
        Add a set of models (X_Ls and X_Ds) to a table (the table does not need to
        already have models).
        
        parameter model_list is a list of dicts, where each dict contains the keys
        X_L, X_D, and iterations.
        """
        ## Model indexing starts at 0 (and is -1 if none exist)
        max_model_id = self.get_max_model_id(tablename)
        for i,m in enumerate(model_list):
            modelid = max_model_id + 1 + i
            self.write_model(tablename, m, modelid)

    def update_models(self, tablename, modelids, X_L_list, X_D_list, diagnostics_dict):
        """
        Overwrite all models by id, and append diagnostic info.
        
        param diagnostics_dict: -> dict[f_z[0, D], num_views, logscore, f_z[0, 1], column_crp_alpha]
        Each of the 5 diagnostics is a 2d array, size #models x #iterations

        Ignores f_z[0, D] and f_z[0, 1], since these will need to be recalculated after all
        inference is done in order to properly incorporate all models.
        """
        models = self.get_models(tablename)
        new_iterations = len(diagnostics_dict['logscore'])

        # models: dict[model_idx] -> dict[X_L, X_D, iterations, column_crp_alpha, logscore, num_views]. Idx starting at 1.
        # each diagnostic entry is a list, over iterations.

        # Add all information indexed by model id: X_L, X_D, iterations, column_crp_alpha, logscore, num_views.
        for idx, modelid in enumerate(modelids):
            model_dict = models[modelid]
            model_dict['X_L'] = X_L_list[idx]
            model_dict['X_D'] = X_D_list[idx]
            model_dict['iterations'] = model_dict['iterations'] + new_iterations
            
            for diag_key in 'column_crp_alpha', 'logscore', 'num_views':
                diag_list = [l[idx] for l in diagnostics_dict[diag_key]]
                if diag_key in model_dict and type(model_dict[diag_key]) == list:
                    model_dict[diag_key] += diag_list
                else:
                    model_dict[diag_key] = diag_list

        # Save to disk
        self.write_models(tablename, models)

    def update_model(self, tablename, X_L, X_D, modelid, diagnostics_dict):
        """
        Overwrite a certain model by id.
        Assumes that diagnostics_dict was from an analyze run with only one model.

        param diagnostics_dict: -> dict[f_z[0, D], num_views, logscore, f_z[0, 1], column_crp_alpha]
        Each of the 5 diagnostics is a 2d array, size #models x #iterations

        Ignores f_z[0, D] and f_z[0, 1], since these will need to be recalculated after all
        inference is done in order to properly incorporate all models.

        models: dict[model_idx] -> dict[X_L, X_D, iterations, column_crp_alpha, logscore, num_views]. Idx starting at 1.
        each diagnostic entry is a list, over iterations.

        """
        model = self.get_models(tablename, modelid)

        model['X_L'] = X_L
        model['X_D'] = X_D
        model['iterations'] = model['iterations'] + len(diagnostics_dict['logscore'])

        # Add all information indexed by model id: X_L, X_D, iterations, column_crp_alpha, logscore, num_views.
        for diag_key in 'column_crp_alpha', 'logscore', 'num_views':
            diag_list = [l[idx] for l in diagnostics_dict[diag_key]]
            if diag_key in model_dict and type(model_dict[diag_key]) == list:
                model_dict[diag_key] += diag_list
            else:
                model_dict[diag_key] = diag_list
        
        self.write_model(tablename, model, modelid)

    def get_model_ids(self, tablename):
        """ Receive a list of all model ids for the table. """
        models = self.get_models(tablename)
        return models.keys()
            
