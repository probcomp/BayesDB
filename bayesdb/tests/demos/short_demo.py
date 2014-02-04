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


####### New demo ########

# select with ordering by similarity
# infer: nans can't be filled in at one confidence level, but can at another
# simulate

#########################

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
#save_name = 'dha_fz'

#cmds.append('estimate dependence probabilities from dha save to %s;' % save_name)
#cmds.append('estimate dependence probabilities from dha for qual_score limit 20')

cmds.append('select %s from dan_kiva limit 20;' % fields_str)
cmds.append('select %s, similarity to 0 from dan_kiva limit 20;' % fields_str)
cmds.append('select %s, similarity to 0 from dan_kiva order by similarity to 0 limit 20;' % fields_str)

cmds.append('select %s from dan_kiva limit 20;' % fields_str)
cmds.append('select %s, similarity to 16 with respect to journal_entries from dan_kiva limit 10 order by similarity to 16 with respect to journal_entries;' % fields_str)

#
return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    v = raw_input()
    if v != 's':
        if cmd[0] == 'e' and 'for' not in cmd:
            print 'http://ec2-184-73-61-8.compute-1.amazonaws.com:8000/%s.png' % save_name
            return_value = client.execute(cmd, pretty=False)
        else:
            return_value = client.execute(cmd)    
        return_values.append(return_value)



# #
#  INFER
# #
cmds = []
cmds.append('select partner_rating, loan_amount, paid_date, default_rate from dan_kiva limit 20;')
cmds.append('infer partner_rating, loan_amount, paid_date, default_rate from dan_kiva with confidence 0.95 limit 20;')

print
return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    v = raw_input()
    if v != 's':
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
#cmds.append('select %s from dan_kiva limit 10 order by similarity to 0;' % fields_str)
field_str = 'loan_amount'
cmds.append('simulate %s from dan_kiva where %s = 4000  TIMES 10' % pop_el(fields_of_interest, field_str))
#cmds.append('select partner_status, partner_rating, delinquent, loan_amount, gender_ratio, default_rate from dan_kiva where default_rate = 40 limit 10')
#field_str = 'default_rate'
#cmds.append('simulate %s from dan_kiva where %s = 40 TIMES 10' % pop_el(fields_of_interest, field_str))
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 0 with respect to default_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to delinquency_rate;' % fields_str)
# cmds.append('select %s from dan_kiva limit 10 order by similarity to 2 with respect to loan_amount;' % fields_str)
#
return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    v = raw_input()
    if v != 's':
        return_value = client.execute(cmd)    
        return_values.append(return_value)

    cmds = []

save_name = 'dha_fz'
cmds = []
cmds.append('estimate dependence probabilities from dha save to %s;' % save_name)
#cmds.append('estimate dependence probabilities from dha for qual_score limit 20')

return_values = []
for cmd in cmds:
    print '>>> client.execute(\'%s\')' % cmd
    v = raw_input()
    if v != 's':
        return_value = client.execute(cmd)    
        return_values.append(return_value)

    cmds = []
