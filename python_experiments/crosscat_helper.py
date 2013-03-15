import os
import sys
import optparse
import cloud
import random

def run_matlab(in_folder, file_base, experiment, n_pred_samples, n_mcmc_iter, sample_folder):

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
    if cloud.status(job_id) == 'done':
        out = cloud.result(job_id)
        values = parse_text(out, experiment)
    else:
        print 'job ' + str(job_id) + ' not done'
        if experiment == 'regression':
            values = [None, None]
        else:
            values = [',,']
    return values

def parse_text(out, experiment):
    out = out.split('#####')
    if experiment == 'regression':
        values = [0]*2
        values[0] = out[1]
        values[1] = out[3]
    if experiment == 'correlation':
        values = [0]*(len(out)/2)
        for i in range(len(values)):
            values[i] = out[2*i + 1]
    return values

def get_job_ids(in_folder, file_base):
    g = open(in_folder + file_base + '-results.csv')
    lines = g.readlines()
    job_ids = map(lambda x: x.strip().split(',')[-1], lines)
    return job_ids

def run(in_folder, file_base, experiment, n_pred_samples, n_mcmc_iter, sample_folder):
    job_id = cloud.call(run_matlab,
                         in_folder,
                         file_base,
                         experiment,
                         n_pred_samples,
                         n_mcmc_iter,
                         sample_folder,
                         _type='c1',
                         _env='matlab',
                         _vol=['crosscat-samples', 'crosscat-data']
                         )
    return job_id
