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

from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)

cmd_list = [
#    'DROP PTABLE jay_dha;',
#    'CREATE PTABLE jay_dha FROM /home/sgeadmin/tabular_predDB/Examples/dha.csv;',
#    'IMPORT SAMPLES dha_samples.pkl.gz INTO jay_dha;',
#    'UPDATE DATATYPES FROM jay_dha FOR name TO key;',
    'SELECT name, hosp_reimb_ratio FROM jay_dha ORDER BY SIMILARITY TO 3 WITH RESPECT TO qual_score LIMIT 10;',
    'SELECT name, hosp_reimb_ratio FROM jay_dha ORDER BY similarity_to(name="Albany NY", qual_score) LIMIT 10;',
    'SELECT name, hosp_reimb_ratio FROM jay_dha ORDER BY similarity_to(3) LIMIT 10;',
    'SELECT name, similarity_to(NAME="Albany NY"), hosp_reimb_ratio FROM jay_dha ORDER BY similarity_to(NAME="Albany NY") LIMIT 10;',
    'SELECT name, hosp_reimb_ratio FROM jay_dha WHERE name="Albany NY";',
    "SELECT mutual_information(hosp_reimb_ratio, hosp_reimb_p_dcd) FROM jay_dha;",
    "SELECT col_anomalousness(qual_score) FROM jay_dha LIMIT 20;",
    "SELECT PROBABILITY(hosp_reimb_ratio=0.8) FROM jay_dha;",
    "SELECT row_anomalousness FROM jay_dha LIMIT 20;",
    "SIMULATE name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM jay_dha WHERE name='Albany NY' TIMES 10;",
    'SELECT name, hosp_reimb_ratio, hosp_reimb_p_dcd, mdcr_spnd_inp, ttl_mdcr_spnd, md_copay_p_dcd, ttl_copay_p_dcd FROM jay_dha LIMIT 10;',
    "SELECT name, hosp_reimb_ratio FROM jay_dha WHERE hosp_reimb_ratio=0.8;",

    'SELECT name, hosp_reimb_ratio, hosp_reimb_p_dcd, mdcr_spnd_inp, ttl_mdcr_spnd, md_copay_p_dcd, ttl_copay_p_dcd FROM jay_dha ORDER BY SIMILARITY TO 0 LIMIT 10;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM jay_dha REFERENCING mdcr_spnd_inp LIMIT 6 SAVE TO dha_fz;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM jay_dha REFERENCING mdcr_spnd_inp SAVE TO dha_full_fz;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM jay_dha REFERENCING mdcr_spnd_inp WITH CONFIDENCE 0.9 SAVE TO dha_fz;',
    ]

for cmd in cmd_list:
    print '>>> %s' % cmd
    user_input = raw_input()
    if user_input == '' or user_input == ' ':
        client.execute(cmd, timing=False)
    else:
        print '>>>'
        client.execute(raw_input(), timing=False)
    
