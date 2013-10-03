print
cmd = '>>> from DatabaseClient import DatabaseClient'
print cmd
raw_input()
from DatabaseClient import DatabaseClient
#
cmd = ">>> client = DatabaseClient(hostname='localhost')"
print cmd
raw_input()
client = DatabaseClient(hostname=None)
#
'''
cmd = 'drop btable dan_kiva;'
print '>>> client.execute(\'%s\')' % cmd
raw_input()
out = client(cmd)
#
cmd = 'create btable dan_kiva from data/kiva.csv;'
print '>>> client.execute(\'%s\')' % cmd
raw_input()
out = client(cmd)
#
cmd = 'import samples data/kiva_flat_table_model_500.pkl.gz into dan_kiva iterations 500;'
print '>>> client.execute(\'%s\')' % cmd
raw_input()
out =client(cmd)
'''
# print client('select * from dan_kiva limit 5;')

####### New demo ########

# select with ordering by similarity
# infer: nans can't be filled in at one confidence level, but can at another
# simulate

#########################

# #
#  ESTIMATE DEPENDENCE
# #
save_name = 'dankiva_fz'
cmds = []
cmds.append('estimate dependence probabilities from dan_kiva save to %s;' % save_name)
cmds.append('estimate dependence probabilities from dan_kiva referencing delinquent limit 10 save to %s;' % save_name)
cmds.append('estimate dependence probabilities from dan_kiva referencing gender_ratio limit 5 save to %s;' % save_name)
#
return_values = []
print
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    raw_input()
    print 'http://ec2-184-73-61-8.compute-1.amazonaws.com:8000/%s.png' % save_name
    return_value = client.execute(cmd, pretty=False)
    return_values.append(return_value)
#


# #
#  ORDER BY SIMILARITY 
# #
fields_of_interest = [
    'journal_entries',
    'num_borrowers',
    'gender_ratio',
    ]
fields_str = ', '.join(fields_of_interest)

cmds = []
cmds.append('select %s, similarity to 0 from dan_kiva limit 20;' % fields_str)
cmds.append('select %s, similarity to 0 from dan_kiva order by similarity to 0 limit 10;' % fields_str)
cmds.append('select %s, similarity to 16 with respect to journal_entries from dan_kiva limit 10;' % fields_str)
cmds.append('select %s, similarity to 16 with respect to journal_entries from dan_kiva limit 10 order by similarity to 16 with respect to journal_entries;' % fields_str)
cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to gender_ratio;' % fields_str)
#
print
return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    raw_input()
    return_value = client.execute(cmd)    
    return_values.append(return_value)

# #
#  SIMULATE
# #
fields_of_interest = [
    'partner_status',
    'partner_rating',
    'delinquent',
    'default_rate',
    'loan_amount',
    'gender_ratio',
    ]
fields_str = ', '.join(fields_of_interest)

def pop_el(in_list, el):
    in_list = list(in_list)
    index = in_list.index(el)
    in_list.pop(index)
    list_str = ', '.join(in_list)
    return list_str, el

cmds = []
cmds.append('select %s from dan_kiva limit 20;' % fields_str)
cmds.append('select %s from dan_kiva limit 10 order by similarity to 0;' % fields_str)
field_str = 'loan_amount'
cmds.append('simulate %s from dan_kiva where %s = 4000  TIMES 10' % pop_el(fields_of_interest, field_str))
cmds.append('select partner_status, partner_rating, delinquent, loan_amount, gender_ratio, default_rate from dan_kiva where default_rate = 40 limit 10')
field_str = 'default_rate'
cmds.append('simulate %s from dan_kiva where %s = 40 TIMES 10' % pop_el(fields_of_interest, field_str))
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 0 with respect to default_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to delinquency_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to loan_amount;' % fields_str)
#
return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    raw_input()
    return_value = client.execute(cmd)    
    return_values.append(return_value)
