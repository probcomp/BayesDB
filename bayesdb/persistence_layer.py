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

class PersistenceLayer(object):
    def drop_btable(self, tablename):
        raise NotImplementedError()

    def list_btables(self):
        raise NotImplementedError()
    
    def delete_model(self, tablename, model_index):
        raise NotImplementedError()
            
    def get_latent_states(self, tablename):
        raise NotImplementedError()
        
    def get_metadata(self, tablename):
        raise NotImplementedError()

    def get_max_model_id(self, tablename):
        raise NotImplementedError()
    
    def get_cctypes(self, tablename):
        raise NotImplementedError()
    
    def update_cctypes(self, tablename, cctypes):
        raise NotImplementedError()
    
    def update_metadata(self, tablename, M_r, M_c, T):
        raise NotImplementedError()
    
    def check_if_table_exists(self, tablename):
        raise NotImplementedError()

    def write_csv(self, tablename, csv):
        raise NotImplementedError()
    
    def create_btable_from_csv(self, tablename, csv_path, cctypes, postgres_coltypes, colnames):
        raise NotImplementedError()

    def add_models(self, tablename, X_L_list, X_D_list, iterations):
        raise NotImplementedError()

    def update_model(self, tablename, X_L, X_D, iterations, modelid):
        raise NotImplementedError()
    
    def insert_models(self, tablename, states_by_model):
        raise NotImplementedError()

    def get_table_id(self, tablename):
        raise NotImplementedError()

    def get_model(self, tablename, modelid):
        raise NotImplementedError()

    def get_model_ids(self, tablename):
        raise NotImplementedError()
            
