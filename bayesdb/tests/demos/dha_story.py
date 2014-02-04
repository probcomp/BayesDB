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

from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)

cmd_list = [
    'DROP PTABLE dha_demo;',
    'CREATE PTABLE dha_demo FROM /home/sgeadmin/tabular_predDB/Examples/dha.csv;',
    'IMPORT SAMPLES dha_samples.pkl.gz INTO dha_demo;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo LIMIT 10;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo SAVE TO dha_z_matrix.png;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score LIMIT 6;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score WITH CONFIDENCE 0.9;', 
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING pymt_p_md_visit LIMIT 6;',
#    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\') LIMIT 10;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\', qual_score), ami_score  LIMIT 10;',
    'SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\', pymt_p_visit_ratio), ttl_mdcr_spnd  LIMIT 10;',
    'SIMULATE name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo WHERE ami_score=95.0  TIMES 10;',
    'SIMULATE name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo WHERE ttl_mdcr_spnd=50000 TIMES 10;',
]

import sys
for cmd in cmd_list:
    sys.stdout.write('>>> %s' % cmd)
    user_input = raw_input()
    if user_input == '' or user_input == ' ':
        client.execute(cmd, timing=False)
    else:
        print '>>>'
        client.execute(raw_input(), timing=False)
    
"""
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 LIMIT 10;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 WITH RESPECT TO qual_score, ami_score  LIMIT 10;',
    'SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 WITH RESPECT TO pymt_p_visit_ratio, ttl_mdcr_spnd  LIMIT 10;',
"""
