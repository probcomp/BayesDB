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

import crosscat.utils.data_utils as du

from bayesdb.persistence_layer import PersistenceLayer
import bayesdb.settings as S


class FilePersistenceLayer(PersistenceLayer):
    """
    Stores btables in the following format in the "data" directory:
    bayesdb/data/
      btable_index.pkl
      <tablename>/
        data.csv
        metadata.pkl
        models.pkl
        column_lists.pkl

    table_index.pkl: list of btable names.
    
    metadata.pkl: dict. keys: M_r, M_c, T, cctypes
    column_lists.pkl: dict. keys: column list names, values: list of column names.
    models.pkl: dict[model_idx] -> dict[X_L, X_D, iterations]. Idx starting at 1.
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
        self.load_btable_index() # sets it to self.btable_index

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
        f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'r')
        metadata = pickle.load(f)
        f.close()
        return metadata

    def write_metadata(self, tablename, metadata):
        metadata_f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'w')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        metadata_f.close()

    def get_models(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'r')
            models = pickle.load(f)
            f.close()
            return models
        except IOError:
            return {}

    def get_column_lists(self, tablename):
        try:
            f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'r')
            column_lists = pickle.load(f)
            f.close()
            return column_lists
        except IOError:
            return dict()

    def add_column_list(self, tablename, column_list_name, column_list):
        column_lists = self.get_column_lists(tablename)
        column_lists[column_list_name] = column_list
        self.write_column_lists(tablename, column_lists)

    def get_column_list(self, tablename, column_list):
        column_lists = self.get_column_lists(tablename)
        if column_list in column_lists:
            return column_lists[column_list]
        else:
            return []

    def write_models(self, tablename, models):
        models_f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'w')
        pickle.dump(models, models_f, pickle.HIGHEST_PROTOCOL)
        models_f.close()

    def write_column_lists(self, tablename, column_lists):
        column_lists_f = open(os.path.join(self.data_dir, tablename, 'column_lists.pkl'), 'w')
        pickle.dump(column_lists, column_lists_f, pickle.HIGHEST_PROTOCOL)
        column_lists_f.close()

    def get_csv(self, tablename):
        f = open(os.path.join(self.data_dir, tablename, 'data.csv'), 'r')
        text = f.read()
        f.close()
        return text

    def write_csv(self, tablename, csv):
        """
        Input: csv is the raw csv data, which gets persisted as data.csv.
        Called by create_btable_from_csv as a helper function.
        """
        if not os.path.exists(os.path.join(self.data_dir, tablename)):
            os.mkdir(os.path.join(self.data_dir, tablename))        
        f = open(os.path.join(self.data_dir, tablename, 'data.csv'), 'w')
        csv_abs_path = os.path.abspath(f.name)
        f.write(csv)
        f.close()
        return csv_abs_path

    def drop_btable(self, tablename):
        """Delete a single btable."""
        if tablename in self.btable_index:
            shutil.rmtree(os.path.join(self.data_dir, tablename))
            self.remove_btable_from_index(tablename)
        return 0
        
    def list_btables(self):
        """Return a list of all btable names."""
        return self.btable_index

    def delete_model(self, tablename, model_index):
        """Delete a single model"""
        models = pickle.load(open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'r'))
        del models[model_index]
        return 0
            
    def get_latent_states(self, tablename):
        """Return X_L_list, X_D_list, and M_c"""
        metadata = self.get_metadata(tablename)
        models = self.get_models(tablename)
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

    def get_max_model_id(self, tablename, models=None):
        """Get the highest model id, and -1 if there are no models.
        Model indexing starts at 0 when models exist."""
        if models is None:
            models = self.get_models(tablename)
        if len(models.keys()) == 0:
            return -1
        else:
            return max(models.keys())

    def get_cctypes(self, tablename):
        """Access the table's current cctypes."""
        metadata = self.get_metadata(tablename)
        return metadata['cctypes']

    def update_schema(self, tablename, mappings):
        """
        mappings is a dict of column name to 'continuous', 'multinomial',
        or an int, which signifies multinomial of a specific type.
        TODO: FIX HACKS. Current works by reloading all the data from csv,
        and it ignores multinomials' specific number of outcomes.
        Also, disastrous things may happen if you update a schema after creating models.
        """
        max_modelid = self.get_max_model_id(tablename)
        if max_modelid is not None and max_modelid > 0:
          return 'Error: cannot update datatypes after models have already been created. Please create a new table.'
          
        metadata = self.get_metadata(tablename)
        cctypes = metadata['cctypes']
        M_c = metadata['M_c']
        M_r = metadata['M_r']
        T = metadata['T']

        # Now, update cctypes, T, M_c, and M_r
        for col, mapping in mappings.items():
          ## TODO: fix this hack! See method's docstring.
          if type(mapping) == int:
            mapping = 'multinomial'
          cctypes[M_c['name_to_idx'][col]] = mapping
        T, M_r, M_c, header = du.read_data_objects(os.path.join(self.data_dir, tablename, 'data.csv'), cctypes=cctypes)

        # Now, put cctypes, T, M_c, and M_r back into the DB
        self.update_metadata(tablename, M_r, M_c, T, cctypes)
        
        return self.get_metadata(tablename)

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

    def check_if_table_exists(self, tablename):
        """Return true iff this tablename exists in the persistence layer."""
        return tablename in self.btable_index

    def create_btable_from_csv(self, tablename, csv_path, csv, cctypes, postgres_coltypes, colnames):
        """
        This function is called to create a btable.
        It creates the table's persistence directory, saves data.csv and metadata.pkl.
        Creates models.pkl as empty dict.
        """
        # Make directory for table
        if not os.path.exists(os.path.join(self.data_dir, tablename)):
            os.mkdir(os.path.join(self.data_dir, tablename))        

        # Write csv
        self.write_csv(tablename, csv)

        # Write metadata
        T, M_r, M_c, header = du.read_data_objects(csv_path, cctypes=cctypes)
        metadata = dict(M_c=M_c, M_r= M_r, T=T, cctypes=cctypes)
        self.write_metadata(tablename, metadata)

        # Write models
        models = dict()
        self.write_models(tablename, models)

        # Write column lists
        column_lists = dict()
        self.write_column_lists(tablename, column_lists)

        # Add to btable name index
        self.add_btable_to_index(tablename)

    def add_models(self, tablename, model_list):
        """
        Add a set of models (X_Ls and X_Ds) to a table (the table does not need to
        already have models).
        
        parameter model_list is a list of dicts, where each dict contains the keys
        X_L, X_D, and iterations.
        """
        # Load from existing models file.
        models = self.get_models(tablename)
        
        ## Model indexing starts at 0 (and is -1 if none exist)
        max_model_id = self.get_max_model_id(tablename, models)        
        for i,m in enumerate(model_list):
            models[max_model_id + 1 + i] = m
        self.write_models(tablename, models)

    def update_models(self, tablename, models_new):
        """ Overwrite all models by id. """
        models = self.get_models(tablename)
        for modelid in models_new.keys():            
            models[modelid] = models_new[modelid]
        self.write_models(tablename, models)

    def update_model(self, tablename, X_L, X_D, iterations, modelid):
        """ Overwrite a certain model by id. """
        models = self.get_models(tablename)
        models[modelid] = dict(X_L=X_L, X_D=X_D, iterations=iterations)
        self.write_models(tablename, models)

    def get_model(self, tablename, modelid):
        """ Retrieve an individual (X_L, X_D, iteration) tuple, by modelid. """
        models = self.get_models(tablename)
        m = models[modelid]
        return m['X_L'], m['X_D'], m['iterations']

    def get_model_ids(self, tablename):
        """ Receive a list of all model ids for the table. """
        models = self.get_models(tablename)
        return models.keys()
            
