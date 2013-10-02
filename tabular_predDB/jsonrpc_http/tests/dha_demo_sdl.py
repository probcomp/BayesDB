from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)

cmd_list = [
    'DROP PTABLE dha_demo;',
    'CREATE PTABLE dha_demo FROM /home/sgeadmin/tabular_predDB/Examples/dha.csv;',
    'IMPORT SAMPLES dha_samples.pkl.gz INTO dha_demo;',
    'SELECT hosp_reimb_ratio, hosp_reimb_p_dcd, mdcr_spnd_inp, ttl_mdcr_spnd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo LIMIT 10;',
    'SELECT hosp_reimb_ratio, hosp_reimb_p_dcd, mdcr_spnd_inp, ttl_mdcr_spnd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo ORDER BY SIMILARITY TO 0 LIMIT 10;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING mdcr_spnd_inp LIMIT 6 SAVE TO dha_fz;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING mdcr_spnd_inp SAVE TO dha_full_fz;',
    'ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING mdcr_spnd_inp WITH CONFIDENCE 0.9 SAVE TO dha_fz;',
    
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
    
