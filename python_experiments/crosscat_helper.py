import sys
import optparse
import condor
import random

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


def run_matlab(file_base, experiment):

    mcr_loc = 'matlab/mcr/v717/'
    
    command = 'sh ./run_run_crosscat.sh '
    command += mcr_loc + ' '
    command += in_folder + ' '
    command += file_base + ' '
    command += experiment + ' '
    command += n_pred_samples + ' '
    command += n_mcmc_iter + ' '
    command += str(random.randint(0, 2**32 - 1)) + ' '
    command += sample_folder + ' '
    out = os.popen(command).read()
    
    return out

def parse_out(experiment, job_id):
    print 'processing job ' + str(job_id)
    if condor.status(job_id) == 'done':
        out = condor.result(job_id)
        out = out.split('#####')
        if experiment == 'regression':
            values = [0]*2
            values[0] = out[1]
            values[1] = out[3]
        if experiment == 'correlation':
            values = [0]*(len(out)/2)
            for i in range(len(values)):
                values[i] = out[2*i + 1]
    else:
        print 'job ' + str(job_id) + ' not done'
        if experiment == 'regression':
            values = [None, None]
        else:
            values = [',,']
    return values

def get_job_ids(file_base):
    g = open(in_folder + file_base + '-results.csv')
    lines = g.readlines()
    job_ids = map(lambda x: x.strip().split(',')[-1], lines)
    return job_ids

def run(file_base, experiment):
    job_id = condor.call(run_matlab,
                         file_base, 
                         experiment,
                         _type='c2',
                         _env='matlab')
    return job_id
