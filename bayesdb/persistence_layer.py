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

from contextlib import contextmanager
import os
import psycopg2
import sys
import crosscat.utils.data_utils as du
import datetime
import json

import bayesdb.settings as S


class PersistenceLayer(object):
    def __init__(self, dbname='sgeadmin', user=os.environ['USER']):
        self.dbname = dbname
        self.user = user
        self.psycopg_connect_str = 'dbname=%s user=%s' % (self.dbname, self.user)

    @contextmanager
    def open_db_connection(self, commit=False):
        conn = psycopg2.connect(self.psycopg_connect_str)
        cur = conn.cursor()
        try:
            yield cur
            if commit:
                conn.commit()            
        except psycopg2.DatabaseError, e:
            sys.stderr.write('Database Error in PersistenceLayer:\n' + str(e))
            raise e
        finally:
            conn.close()
    
    def start_from_scratch(self):
        # drop
        cmd_str = 'dropdb -U %s %s' % (self.user, self.dbname)
        os.system(cmd_str)
        # create
        cmd_str = 'createdb -U %s %s' % (self.user, self.dbname)
        os.system(cmd_str)
        #
        script_filename = os.path.join(S.path.this_repo_dir,
                                       'install_scripts/table_setup.sql')
        cmd_str = 'psql %s %s -f %s' % (self.dbname, self.user, script_filename)
        os.system(cmd_str)

    def drop_and_load_db(self, filename):
        if not os.path.isfile(filename):
          raise_str = 'drop_and_load_db(%s): filename does not exist' % filename
          raise Exception(raise_str)
        # drop
        cmd_str = 'dropdb %s' % dbname
        os.system(cmd_str)
        # create
        cmd_str = 'createdb %s' % dbname
        os.system(cmd_str)
        # load
        if filename.endswith('.gz'):
          cmd_str = 'gunzip -c %s | psql %s %s' % (filename, dbname, user)
        else:
          cmd_str = 'psql %s %s < %s' % (dbname, user, filename)
        os.system(cmd_str)

    def drop_btable(self, tablename):
        with self.open_db_connection(commit=True) as cur:
            cur.execute('DROP TABLE IF EXISTS %s' % tablename)
            cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            tableids = cur.fetchall()
            for tid in tableids:
                tableid = tid[0]
                cur.execute("DELETE FROM preddb.models WHERE tableid=%s;", (tableid,))
                cur.execute("DELETE FROM preddb.table_index WHERE tableid=%s;", (tableid,))
        return 0

    def list_btables(self):
        with self.open_db_connection(commit=True) as cur:
            cur.execute("SELECT tablename FROM preddb.table_index;")
            tablenames = cur.fetchall()
        return [t[0] for t in tablenames]

    def delete_chain(self, tablename, chain_index):
        with self.open_db_connection(commit=True) as cur:
            cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            tableids = cur.fetchall()
            for tid in tableids:
                tableid = tid[0]
                cur.execute("DELETE FROM preddb.models WHERE tableid=%s;", (tableid,))
                cur.execute("DELETE FROM preddb.table_index WHERE tableid=%s;", (tableid,))
        return 0
            
    def get_latent_states(self, tablename):
        """Return X_L_list, X_D_list, and M_c"""
        with self.open_db_connection() as cur:
          cur.execute("SELECT tableid, m_c FROM preddb.table_index WHERE tablename=%s;", (tablename,))
          tableid, M_c_json = cur.fetchone()
          M_c = json.loads(M_c_json)
          cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%s;", (tableid,))
          chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
          chainids = map(int, chainids)
          X_L_list = list()
          X_D_list = list()
          for chainid in chainids:
            cur.execute("SELECT x_l, x_d FROM preddb.models WHERE tableid=%s AND chainid=%s AND " 
                      + "iterations=(SELECT MAX(iterations) FROM preddb.models WHERE tableid=%s AND chainid=%s);", (tableid, chainid, tableid, chainid))
            X_L_prime_json, X_D_prime_json = cur.fetchone()
            X_L_list.append(json.loads(X_L_prime_json))
            X_D_list.append(json.loads(X_D_prime_json))
        return (X_L_list, X_D_list, M_c)
        
    def get_metadata_and_table(self, tablename):
        """Return M_c and M_r and T"""
        with self.open_db_connection() as cur:
            cur.execute("SELECT m_c, m_r, t FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            M_c_json, M_r_json, t_json = cur.fetchone()
            M_c = json.loads(M_c_json)
            M_r = json.loads(M_r_json)
            T = json.loads(t_json)
        return M_c, M_r, T

    def get_max_chain_id(self, tablename):
        with self.open_db_connection() as cur:
            cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            tableid = cur.fetchone()[0]
            cur.execute("SELECT MAX(chainid) FROM preddb.models WHERE tableid=%s;", (tableid,))
            max_chainid = cur.fetchone()[0]
            if max_chainid is None:
                max_chainid = 0
        return max_chainid

    def get_cctypes(self, tablename):
        with self.open_db_connection() as cur:
            cur.execute("SELECT cctypes, t, m_r, m_c, path FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            cctypes_json = cur.fetchone()
            cctypes = json.loads(cctypes_json)
        return cctypes

    def update_cctypes(self, tablename, cctypes):
        with self.open_db_connection(commit=True) as cur:
            cur.execute("UPDATE preddb.table_index SET cctypes=%s WHERE tablename=%s;", (json.dumps(cctypes), tablename))

    def update_metadata_and_table(self, tablename, M_r, M_c, T):
        with self.open_db_connection(commit=True) as cur:
            cur.execute("UPDATE preddb.table_index SET m_r=%s, m_c=%s, t=%s WHERE tablename=%s;", (json.dumps(m_r), json.dumps(m_c), json.dumps(t), tablename))

    def execute_sql(self, sql_string, args=None, commit=False):
        with self.open_db_connection(commit=commit) as cur:
            if args:
                cur.execute(sql_string, args)
            else:
                cur.execute(sql_string)

    def check_if_table_exists(self, tablename):
        ret = False
        with self.open_db_connection() as cur:
            cur.execute("select exists(select * from information_schema.tables where table_name=%s);", (tablename,))
            if cur.fetchone()[0]:
                ret = True
        return ret

    def write_csv(self, tablename, csv):
        # Write csv to file
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(cur_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        f = open(os.path.join(data_dir, '%s.csv' % tablename), 'w')
        csv_abs_path = os.path.abspath(f.name)
        f.write(csv)
        f.close()
        os.chmod(csv_abs_path, 0755)
    
        return csv_abs_path

    def create_btable_from_csv(self, tablename, csv_path, cctypes, postgres_coltypes, colnames):
        with self.open_db_connection(commit=True) as cur:
            ## TODO: warning: m_r and m_c have 0-indexed indices
            ##       but the db has 1-indexed keys
            t, m_r, m_c, header = du.read_data_objects(csv_path, cctypes=cctypes)
            curtime = datetime.datetime.now().ctime()
            cur.execute("INSERT INTO preddb.table_index (tablename, numsamples, uploadtime, analyzetime, t, m_r, m_c, cctypes, path) VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s);", (tablename, 0, curtime, json.dumps(t), json.dumps(m_r), json.dumps(m_c), json.dumps(cctypes), csv_path))

    def add_samples(self, tablename, X_L_list, X_D_list, iterations):
        tableid = self.get_table_id(tablename)
        max_chainid = self.get_max_chain_id(tablename)
        if max_chainid is None: max_chainid = -1
        with self.open_db_connection(commit=True) as cur:
            curtime = datetime.datetime.now().ctime()
            ## TODO: This is dangerous. M_c and cctypes will be out of date. Need to update cctypes.
            #cur.execute("UPDATE preddb.table_index SET m_c=%s, t=%s WHERE tablename=%s;", (json.dumps(M_c), json.dumps(T), tablename))
            for idx, (X_L, X_D) in enumerate(zip(X_L_list, X_D_list)):
                chain_index = max_chainid + 1 + idx
                cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) VALUES (%s, %s, %s, %s, %s, %s);", (tableid, json.dumps(X_L), json.dumps(X_D), curtime, chain_index, iterations))
        return 0

    def add_samples_for_chain(self, tablename, X_L, X_D, iterations, chainid):
        tableid = self.get_table_id(tablename)
        with self.open_db_connection(commit=True) as cur:
            curtime = datetime.datetime.now().ctime()
            cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) " + \
                            "VALUES (%s, %s, %s, %s, %s, %s);",
                        (tableid, json.dumps(X_L), json.dumps(X_D), curtime, chainid, iterations))

    def insert_models(self, tablename, states_by_chain):
        tableid = self.get_table_id(tablename)
        with self.open_db_connection(commit=True) as cur:
            curtime = datetime.datetime.now().ctime()
            for chain_index, (x_l_prime, x_d_prime) in enumerate(states_by_chain):
                cur.execute("INSERT INTO preddb.models (tableid, X_L, X_D, modeltime, chainid, iterations) VALUES (%s, %s, %s, %s, %s, 0);", (tableid, json.dumps(x_l_prime), json.dumps(x_d_prime), curtime, chain_index))
                         

    def get_table_id(self, tablename):
        with self.open_db_connection() as cur:
            cur.execute("SELECT tableid FROM preddb.table_index WHERE tablename=%s;", (tablename,))
            tableid = int(cur.fetchone()[0])
        return tableid

    def get_chain(self, tablename, chainid):
        tableid = self.get_table_id(tablename)
        with self.open_db_connection() as cur:
            cur.execute("SELECT x_l, x_d, iterations FROM preddb.models"
                        + " WHERE tableid=%s AND chainid=%s"
                        + " AND iterations=("
                        + " SELECT MAX(iterations) FROM preddb.models WHERE tableid=%s AND chainid=%s);", (tableid, chainid, tableid, chainid))
      
            X_L_prime_json, X_D_prime_json, prev_iterations = cur.fetchone()
            X_L_prime = json.loads(X_L_prime_json)
            X_D_prime = json.loads(X_D_prime_json)
        return X_L_prime, X_D_prime, prev_iterations

    def get_chain_ids(self, tablename):
        tableid = self.get_table_id(tablename)
        with self.open_db_connection() as cur:
            cur.execute("SELECT DISTINCT(chainid) FROM preddb.models WHERE tableid=%s;", (tableid,))
            chainids = [my_tuple[0] for my_tuple in cur.fetchall()]
            chainids = map(int, chainids)
        return chainids
            
