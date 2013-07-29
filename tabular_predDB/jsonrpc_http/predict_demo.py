import tabular_predDB.python_utils.file_utils as fu
cctypes = fu.unpickle('kiva_cctypes.pkl.gz')

from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)
client('drop btable dan_kiva;')
client('create btable dan_kiva from data/kiva.csv;')
client('import samples data/kiva_flat_table_model_500.pkl.gz into dan_kiva iterations 500;')
print client('select * from dan_kiva limit 5;')

fields_of_interest = [
    'partner_status',
    'partner_rating',
    'delinquent',
    'default_rate',
    'loan_amount',
    'gender_ratio',
    ]
fields_str = ', '.join(fields_of_interest)

cmds = []
cmds.append('select %s from dan_kiva limit 20;' % fields_str)
cmds.append('select %s from dan_kiva limit 10 order by similarity to 0;' % fields_str)
cmds.append('simulate %s from dan_kiva where loan_amount = 4000  TIMES 10' % fields_str)
cmds.append('simulate %s from dan_kiva where default_rate = 20 TIMES 10' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 0 with respect to default_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to delinquency_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to loan_amount;' % fields_str)
#
return_values = []
for cmd in cmds:
    print '>>> %s' % cmd
    return_value = client.execute(cmd)    
    return_values.append(return_value)
