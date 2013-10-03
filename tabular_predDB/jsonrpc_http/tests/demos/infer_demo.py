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
cmds.append('infer partner_rating from dan_kiva with confidence 0.0 limit 20;')
#
return_values = []
for cmd in cmds:
    print '>>> %s' % cmd
    return_value = client.execute(cmd)    
    return_values.append(return_value)
