from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)
#print client.execute('start from scratch;')

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
    client.execute(cmd, timing=True)    

