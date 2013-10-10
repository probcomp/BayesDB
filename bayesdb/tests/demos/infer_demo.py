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
