
def run_ring(i):
    pars = [[0.1], [0.3], [0.5], [0.7], [0.9]]
    par_names = ['width']
    run_corr_exp('ring-i-' + str(i))
    
def run_correlation(i):
    ns = [5, 10, 25, 50, 100]    
    corrs = np.array(range(0,11))/10.0
    pars = []
    for i in range(len(ns)):
        for j in range(len(corrs)):
            pars += [[ns[i], corrs[j]]]
    par_names = ['n', 'corr']
    run_corr_exp('correlation-i-' + str(i))
    
def run_outliers(i):
    pars = [[1], [5], [10], [25], [50]]
    par_names = ['n']
    run_corr_exp('outliers-i-' + str(i))

def run_outliers_correlated(i):
    pars = [[1], [5], [10], [25], [50]]
    par_names = ['n']
    run_corr_exp('outliers-correlated-i-' + str(i))

def run_correlated_halves(i):
    pars = [[25, 0.5], [50, 0.3], [100, 0.2]]
    par_names = ['n', 'corr']
    run_corr_exp('correlated-halves-i-' + str(i))

def run_correlated_pairs(file_base):
    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    pars = []
    for i in range(len(ns)):
        for j in range(len(corrs)):
            pars += [[ns[i], corrs[j]]]
    run_corr_exp('correlated-pairs-i-' + str(i))

def run_corr_exp(file_base):
    
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
        
        for j in range(hist_reps):
            if parse:
                job_id = int(job_ids[k])
                k += 1
                h = parse_out('correlation', job_id)
                for l in range(len(h)):
                    f.write(','.join(map(str, pars[i] + [j])) + ',' + h[l] + '\n')
            else:
                job_id = run(name, 'correlation')
                f.write(','.join(map(str, pars + [j,job_id])) + '\n')
                             
    f.close()

