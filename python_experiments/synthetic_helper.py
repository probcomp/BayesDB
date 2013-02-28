from crosscat_helper import *
import numpy as np

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

class Experiment:

    def __init__(self, hist_reps, n_pred_samples, n_mcmc_iter):
        self.hist_reps = hist_reps
        self.n_pred_samples = n_pred_samples
        self.n_mcmc_iter = n_mcmc_iter

    def run_ring(self, i):
        pars = [[0.1], [0.3], [0.5], [0.7], [0.9]]
        par_names = ['width']
        self.run_corr_exp('ring-i-' + str(i), pars, par_names)
    
    def run_correlation(self, i):
        ns = [5, 10, 25, 50, 100]    
        corrs = np.array(range(0,11))/10.0
        pars = []
        for i in range(len(ns)):
            for j in range(len(corrs)):
                pars += [[ns[i], corrs[j]]]
        par_names = ['n', 'corr']
        self.run_corr_exp('correlation-i-' + str(i), pars, par_names)
        
    def run_outliers(self, i):
        pars = [[1], [5], [10], [25], [50]]
        par_names = ['n']
        self.run_corr_exp('outliers-i-' + str(i), pars, par_names)
        
    def run_outliers_correlated(self, i):
        pars = [[1], [5], [10], [25], [50]]
        par_names = ['n']
        self.run_corr_exp('outliers-correlated-i-' + str(i), pars, par_names)
        
    def run_correlated_halves(self, i):
        pars = [[25, 0.5], [50, 0.3], [100, 0.2]]
        par_names = ['n', 'corr']
        self.run_corr_exp('correlated-halves-i-' + str(i), pars, par_names)
    
    def run_correlated_pairs(self, i):
        ns = [5, 25, 50, 100, 200]    
        corrs = np.array(range(0,11))/10.0
        pars = []
        for i in range(len(ns)):
            for j in range(len(corrs)):
                pars += [[ns[i], corrs[j]]]
        self.run_corr_exp('correlated-pairs-i-' + str(i), pars, par_names)

    def run_corr_exp(self, file_base, pars, par_names):

        f = open(out_folder + file_base + '-results.csv', 'w')
        if parse:
            job_ids = get_job_ids(file_base)
            header = ','.join(par_names + ['rep,i,j,mutual_info\n']) 
            f.write(header)

        k = 0
        for i in range(len(pars)):

            file_suffix = ''
            for s in range(len(par_names)):
                file_suffix += '-' + par_names[s] + '-' + str(pars[i][s])

            name = file_base + file_suffix

            for j in range(self.hist_reps):
                if parse:
                    job_id = int(job_ids[k])
                    k += 1
                    h = parse_out('correlation', job_id)
                    for l in range(len(h)):
                        f.write(','.join(map(str, pars[i] + [j])) + ',' + h[l] + '\n')
                else:
                    job_id = run(in_folder,
                                 name,
                                 'correlation',
                                 self.n_pred_samples,
                                 self.n_mcmc_iter,
                                 sample_folder)
                    f.write(','.join(map(str, pars + [j,job_id])) + '\n')

        f.close()

