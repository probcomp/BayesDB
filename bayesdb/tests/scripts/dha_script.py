from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)
#print client.execute('start from scratch;')

cmds = []
#cmds.append('drop ptable dha;')
'''
cmds.append('create ptable dha from /home/sgeadmin/tabular_predDB/Examples/dha.csv;')
cmds.append('create 10 models for dha;')
cmds.append('analyze dha for 10 iterations;')
cmds.append('analyze dha for 10 iterations;')
cmds.append('analyze dha for 30 iterations;')
cmds.append('analyze dha for 50 iterations;')
cmds.append('analyze dha for 100 iterations;')
cmds.append('analyze dha for 100 iterations;')
cmds.append('analyze dha for 100 iterations;')
cmds.append('analyze dha for 100 iterations;')
'''
'''
cmds.append('select * from dha limit 5;')
cmds.append('export from dha to dha_samples;')

cmds.append('create ptable dha_loaded from /home/sgeadmin/tabular_predDB/Examples/dha.csv;')
cmds.append('import samples dha_samples.pkl.gz into dha_loaded;')
cmds.append('select * from dha limit 5;')
'''

cmds.append('drop ptable dha_big')
#cmds.append('create ptable dha_big from /home/sgeadmin/tabular_predDB/Examples/demo_data/DHA/DAP_Hosp.dat;')
cmds.append('create ptable dha_big from /home/sgeadmin/tabular_predDB/Examples/dha.csv;')
cmds.append('import samples dha_samples.pkl.gz INTO dha_big;')
cmds.append('create 10 models for dha_big;')
cmds.append('analyze dha_big for 2 iterations;')
cmds.append('analyze dha_big for 98 iterations;')
cmds.append('analyze dha_big for 100 iterations;')
cmds.append('analyze dha_big for 100 iterations;')
cmds.append('analyze dha_big for 100 iterations;')
cmds.append('analyze dha_big for 100 iterations;')
cmds.append('export from dha_big to dha_samples_2;')



'''
cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20;')
cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0;')
cmds.append('select dayofweek, deptime, crsdeptime, actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0 with respect to actualelapsedtime;')
cmds.append('select dayofweek, actualelapsedtime, similarity to 0 with respect to actualelapsedtime from jayt where distance > 800 limit 20 order by similarity to 0 with respect to actualelapsedtime, dayofweek;')
cmds.append('select dayofweek, actualelapsedtime, similarity to 0 from jayt where distance > 800 limit 5;')
cmds.append('select dayofweek, actualelapsedtime, arrtime, similarity to 0 with respect to arrtime from jayt where distance > 800 limit 5 order by similarity to 0 with respect to arrtime, dayofweek;')

cmds.append('select probability(actualelapsedtime=200) from jayt where distance > 800 limit 20;')
# cmds.append('select * from jayt limit 5;')
cmds.append('infer actualelapsedtime from jayt with confidence 0.8 limit 20;')

cmds.append('simulate dayofweek, deptime, crsdeptime FROM jayt where dayofweek = 7 TIMES 3;')
cmds.append('estimate dependence probabilities from jayt;')
cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime limit 6 save to fz;')
cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime with confidence 0.5;')
'''
#cmds.append('drop ptable jayt;')
#cmds.append('estimate dependence probabilities from dan_kiva referencing activity limit 10 save to activity_z;')

#cmds.append('select * from dha_small;')
#cmds.append('select probability(mdcr_spnd_outp=1), probability(mdcr_spnd_outp=2), probability(mdcr_spnd_outp=3) from dha_small;')

for cmd in cmds:
    print '>>> %s' % cmd
    client.execute(cmd, timing=True)    

