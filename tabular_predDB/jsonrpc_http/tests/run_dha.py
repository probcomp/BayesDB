from DatabaseClient import DatabaseClient
client = DatabaseClient(hostname=None)
#print client.execute('start from scratch;')

cmds = []
#cmds.append('select * from dha limit 20;')
#cmds.append('drop ptable dha;')
#cmds.append('create ptable dha from /home/sgeadmin/tabular_predDB/Examples/dha.csv;')
#cmds.append('create 20 models for dha;')
cmds.append('analyze dha for 10 iterations;')
cmds.append('analyze dha for 10 iterations;')
cmds.append('analyze dha for 30 iterations;')
cmds.append('analyze dha for 50 iterations;')
cmds.append('analyze dha for 50 iterations;')
cmds.append('analyze dha for 50 iterations;')
cmds.append('analyze dha for 50 iterations;')



#cmds.append('select probability(dayofweek=7) from jayt where distance > 800 limit 20;')
# cmds.append('select * from jayt limit 5;')
# cmds.append('infer actualelapsedtime from jayt with confidence 0.0 limit 20;')
# cmds.append('simulate dayofweek, deptime, crsdeptime FROM jayt where dayofweek = 7 TIMES 3;')
# cmds.append('estimate dependence probabilities from jayt;')
# cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime limit 6 save to fz;')
# cmds.append('estimate dependence probabilities from jayt referencing actualelapsedtime with confidence 0.5;')
# cmds.append('drop ptable jayt;')
#cmds.append('estimate dependence probabilities from dan_kiva referencing activity limit 10 save to activity_z;')

for cmd in cmds:
    print '>>> %s' % cmd
    client.execute(cmd)    

