from crosscat_helper import *
import numpy as np

hist_reps = 10#10
n_pred_samples = '250'#'250'
n_mcmc_iter = '500'#'500'

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
    in_folder = '../../cluster/'
    out_folder = '../../crosscat-results/'
else:
    in_folder = '../../data/'
    out_folder = '../../cluster/'
    sample_folder = '../../crosscat-samples/'

file_base = 'dha'

f = open(out_folder + file_base + '-results.csv', 'w')
if parse:
    job_ids = get_job_ids(in_folder, file_base)
    header = 'rep,i,j,mutual_info\n'
    f.write(header)

for i in range(hist_reps):
    if parse:
        job_id = int(job_ids[i])
        h = parse_out('correlation', job_id)
        for j in range(len(h)):
            f.write(str(i) + ',' + h[j] + '\n')
    else:
        job_id = run(in_folder,
                     file_base,
                     'correlation',
                     n_pred_samples,
                     n_mcmc_iter,
                     sample_folder)
        f.write(str(i) + ',' + str(job_id) + '\n')

f.close()

