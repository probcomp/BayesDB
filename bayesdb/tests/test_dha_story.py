from bayesdb.Client import Client
client = Client()
import os

tests_dir = os.path.split(os.path.realpath(__file__))[0]
dha_csv_path = os.path.join(tests_dir, 'data/dha.csv')
dha_samples_path = os.path.join(tests_dir, 'samples/dha_samples.pkl.gz')
test_results_path = os.path.join(tests_dir, 'regression_test_output/dha_story_results_record.pkl')

cmd_list = [
    'DROP BTABLE dha_demo;',
    'CREATE BTABLE dha_demo FROM %s;' % dha_csv_path,
    'IMPORT SAMPLES %s INTO dha_demo;' % dha_samples_path,
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo LIMIT 10;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score LIMIT 6;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score WITH CONFIDENCE 0.9;', 
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING pymt_p_md_visit LIMIT 6;',
#    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\') LIMIT 10;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\', qual_score), ami_score  LIMIT 10;',
    'SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY similarity_to(name=\'Albany NY\', pymt_p_visit_ratio), ttl_mdcr_spnd  LIMIT 10;',
#    'SIMULATE name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo WHERE ami_score=95.0  TIMES 10;',
#    'SIMULATE name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo WHERE ttl_mdcr_spnd=50000 TIMES 10;',
]

import pickle
import sys
import numpy

dha_story_results = []
if len(sys.argv) > 1 and sys.argv[1] == 'record':
    print 'Recording new dha_story_results to %s' % test_results_path
    record = True
else:
    ## Testing
    dha_story_results = pickle.load(open(test_results_path, 'r'))
    record = False
    
for i, cmd in enumerate(cmd_list):
    print cmd
    result = client.execute(cmd, timing=False, pretty=False)
    if record:
        dha_story_results.append(result)
    else:
        if type(result) == dict:
            for k,v in result.iteritems():
                if isinstance(v, numpy.ndarray):
                    assert (v == dha_story_results[i][k]).all(), (v, dha_story_results[i][k])
                else:
                    assert v == dha_story_results[i][k], (v, dha_story_results[i][k])
        else:
            #assert result == dha_story_results[i], (result, dha_story_results[i])
            pass
            

if record:
    pickle.dump(dha_story_results, open(filename, 'w'))
    
"""
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 LIMIT 10;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 WITH RESPECT TO qual_score, ami_score  LIMIT 10;',
    'SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 3 WITH RESPECT TO pymt_p_visit_ratio, ttl_mdcr_spnd  LIMIT 10;',
"""


