#
#   Copyright (c) 2010-2013, MIT Probabilistic Computing Project
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
import crosscat.utils.data_utils as du
import datetime
import json

from bayesdb.persistence_layer import PersistenceLayer
import bayesdb.settings as S


class FilePersistenceLayer(PersistenceLayer):
    """
    Stores btables in the following format in the "data" directory:
    bayesdb/data/
      tablename1/
        data.csv
        metadata.pkl
        models.pkl
    """
    
    def __init__(self):
        ## Create data directory if doesn't exist
        self.cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.cur_dir, 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.btable_names = set()

    def get_metadata(self, tablename):
        return pickle.load(open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'r'))

    def get_models(self, tablename):
        return pickle.load(open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'r'))

    def get_csv(self, tablename):
        return open(os.path.join(self.data_dir, tablename, 'data.csv'), 'r').read()

    def start_from_scratch(self):
        """Delete all tables and all data."""
        ## TODO: prompt user to confirm
        os.rmdir(self.data_dir)
        os.makedirs(self.data_dir)

    def drop_btable(self, tablename):
        """Delete a single btable."""
        if tablename in self.btable_names:
            os.rmdir(os.path.join(self.data_dir, tablename))
            self.btable_names.remove(tablename)
        return 0

    def list_btables(self):
        """Return a list of all btable names."""
        return self.btable_names

    def delete_chain(self, tablename, chain_index):
        """Delete a single chain(model)"""
        models = pickle.load(open(os.path.jsoin(self.data_dir, tablename, 'models.pkl'), 'r'))
        del models[chain_index]
        return 0
            
    def get_latent_states(self, tablename):
        """Return X_L_list, X_D_list, and M_c"""
        metadata = self.get_metadata(tablename)
        models = self.get_models(tablename)
        M_c = metadata['M_c']
        X_L_list = [model['X_L_list'] for model in models.values()]
        X_D_list = [model['X_D_list'] for model in models.values()]
        return (X_L_list, X_D_list, M_c)
        
    def get_metadata_and_table(self, tablename):
        """Return M_c and M_r and T"""
        metadata = self.get_metadata(tablename)
        M_c = metadata['M_c']
        M_r = metadata['M_r']
        T = metadata['T']
        return M_c, M_r, T

    def get_max_chain_id(self, tablename, models=None):
        """Get the highest chain(model) id."""
        if models is None:
            models = self.get_models(tablename)
        iter_list = [model['iterations'] for model in model.values()]
        if len(iter_list) == 0:
            return 0
        else:
            return max(iter_list)

    def get_cctypes(self, tablename):
        metadata = self.get_metadata(tablename)
        return metadata['cctypes']

    def update_cctypes(self, tablename, cctypes):
        f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'rw'))
        metadata = pickle.load(f)
        metadata['cctypes'] = cctypes
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)

    def update_metadata_and_table(self, tablename, M_r, M_c, T):
        f = open(os.path.join(self.data_dir, tablename, 'metadata.pkl'), 'rw')
        metadata = pickle.load(f)
        metadata['M_r'] = M_r
        metadata['M_c'] = M_c
        metadata['T'] = T
        pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)

    def check_if_table_exists(self, tablename):
        return tablename in self.btable_names

    def write_csv(self, tablename, csv):
        f = open(os.path.join(self.data_dir, tablename, 'data.csv'), 'w')
        csv_abs_path = os.path.abspath(f.name)
        f.write(csv)
        f.close()
        return csv_abs_path

    def create_btable_from_csv(self, tablename, csv_path, cctypes, postgres_coltypes, colnames):
        t, m_r, m_c, header = du.read_data_objects(csv_path, cctypes=cctypes)
        self.write_csv(tablename, csv)
        metadata = dict()
        metadata['M_c'] = m_c
        metadata['M_r'] = m_r
        metadata['T'] = t
        metadata_f = open(os.path.join(self.data_dir, tablane, 'metadata.pkl'), 'w')
        pickle.dump(metadata, metadata_f, pickle.HIGHEST_PROTOCOL)
        self.btable_names.add(tablename)

    def add_samples(self, tablename, X_L_list, X_D_list, iterations):
        assert len(X_L_list) == len(X_D_list)
        f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'rw')
        models = pickle.load(f)
        max_chain_id = self.get_max_chain_id(tablename, models)
        for i in range(len(X_L_list)):
            models[max_chain_id + 1 + i] = dict(X_L=X_L_list[i], X_D=X_D_list[i], iterations=iterations)
        pickle.dump(models, f, pickle.HIGHEST_PROTOCOL)
        return 0

    def add_samples_for_chain(self, tablename, X_L, X_D, iterations, chainid):
        f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'rw')
        models = pickle.load(f)
        models[chainid] = dict(X_L=X_L, X_D=X_D, iterations=iterations)
        pickle.dump(models, f, pickle.HIGHEST_PROTOCOL)

    def insert_models(self, tablename, states_by_chain)
        f = open(os.path.join(self.data_dir, tablename, 'models.pkl'), 'rw')
        models = pickle.load(f)
        models[chainid] = dict(X_L=X_L, X_D=X_D, iterations=iterations)
        pickle.dump(models, f, pickle.HIGHEST_PROTOCOL)
        for chain_index, (x_l_prime, x_d_prime) in enumerate(states_by_chain):
            models[chain_index] = dict(X_L=X_L, X_D=X_D, iterations=0)

    def get_chain(self, tablename, chainid):
        models = self.get_models(tablename)
        m = models[chainid]
        return m['X_L'], m['X_D'], m['iterations']

    def get_chain_ids(self, tablename):
        models = self.get_models(tablename)
        return models.keys()
            
