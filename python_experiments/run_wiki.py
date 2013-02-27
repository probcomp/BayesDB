import sys
import optparse
import condor
import random
import crosscat_helper as cc

parser = optparse.OptionParser()

parser.set_defaults(parse=False, run=False)
parser.add_option("-r", "--run", action="store_true", dest="run")
parser.add_option("-p", "--parse", action="store_true", dest="parse")
(options, args) = parser.parse_args()

parse = options.parse
run_script = options.run
if parse + run_script > 1:
    sys.exit("You must choose only one of running or parsing!")    
if parse + run_script == 0:
    sys.exit("You must choose to either parse or run!")

if parse:
    in_folder = '../../condor/'
    out_folder = '../../crosscat-results/'
else:
    in_folder = '../../data/'
    out_folder = '../../condor/'
    sample_folder = '../../crosscat-samples/'

def run(file_base, experiment):
    job_id = condor.call(cc.run_matlab,
                         file_base, 
                         experiment,
                         _type='c2',
                         _env='matlab')
    return job_id


hist_reps = 1#5
n_pred_samples = '1'#'250'
n_mcmc_iter = '1'#'500'
datasets = [1]

file_base = 'wiki'

f = open(out_folder + file_base + '-results.csv', 'w')
if parse:
    job_ids = cc.get_job_ids(file_base)
    f.write('index,rep,mutual_info\n')
    
k = 0
for j in range(hist_reps):
    for i in datasets:
        
        if parse:
            job_id = int(job_ids[k])
            k += 1
            h = cc.parse_out('correlation', job_id)[0].split(',')[2]
            f.write(str(i) + ',' + str(j) + ',' + h + '\n')
        else:
            name = file_base + '-i-' + str(i)
            job_id = run(name, 'correlation')
            f.write(str(i) + ',' + str(j) + ',' + str(job_id) + '\n')

f.close()
