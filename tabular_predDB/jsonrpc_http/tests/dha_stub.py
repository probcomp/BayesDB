from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)

cmd_list = [
    'DROP PTABLE dha_demo;',
    'CREATE PTABLE dha_demo FROM /home/sgeadmin/tabular_predDB/Examples/dha.csv;',
    'IMPORT SAMPLES dha_samples.pkl.gz INTO dha_demo;',
    'SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha_demo LIMIT 10;',
]

for cmd in cmd_list:
    print '>>> %s' % cmd
    user_input = raw_input()
    if user_input == '' or user_input == ' ':
        client.execute(cmd, timing=False)
    
while user_input != 'exit':
    print '>>>'
    user_input = raw_input()
    client.execute(user_input, timing=False)
