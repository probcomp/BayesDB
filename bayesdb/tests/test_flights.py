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

from bayesdb.Client import Client


def test_flights():
    client = Client()

    cmds = []
    cmds.append('drop ptable jayt;')
    cmds.append('create ptable jayt from /home/sgeadmin/tabular_predDB/Examples/flight_data_subset.csv;')
    #cmds.append('update datatypes from jayt set deptime=categorical(7);')
    cmds.append('create 2 models for jayt;')
    cmds.append('analyze jayt for 1 iterations;')
    cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20;')
    cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0;')
    cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0 with respect to actualelapsedtime;')
    cmds.append('select dayofweek, actualelapsedtime, similarity to 0 with respect to actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0 with respect to actualelapsedtime, dayofweek;')
    cmds.append('select dayofweek, actualelapsedtime, similarity to 0 from jayt where distance > 800 limit 5;')
    cmds.append('select dayofweek, actualelapsedtime, arrtime, similarity to 0 with respect to arrtime from jayt where distance > 800 limit 5 order by similarity to 0 with respect to arrtime, dayofweek;')

    cmds.append('select probability(actualelapsedtime=200) from jayt where distance > 800 limit 20;')
    # cmds.append('select * from jayt limit 5;')
    #cmds.append('infer actualelapsedtime from jayt with confidence 0.8 limit 20;')

    cmds.append('simulate dayofweek, deptime, crsdeptime FROM jayt where dayofweek = 7 TIMES 3;')
    cmds.append('estimate dependence probabilities from jayt;')
    cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime limit 6 save to fz;')
    cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime with confidence 0.5;')
    #cmds.append('drop ptable jayt;')
    #cmds.append('estimate dependence probabilities from dan_kiva referencing activity limit 10 save to activity_z;')

    #cmds.append('select * from dha_small;')
    #cmds.append('select probability(mdcr_spnd_outp=1), probability(mdcr_spnd_outp=2), probability(mdcr_spnd_outp=3) from dha_small;')

    for cmd in cmds:
        print '>>> %s' % cmd
        result = client.execute(cmd, timing=True)
        print result

