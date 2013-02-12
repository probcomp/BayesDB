import cloud
import numpy as np
import math
import matplotlib.pyplot as plt

parse = False

if parse:
    out_folder = '../../crosscat-results/'
else:
    in_folder = './data/'
    out_folder = '../../picloud/'

data_reps = 1
hist_reps = 2
n_chains = '2'
n_pred_samples = '2'
n_mcmc_iter = '2'

def run_matlab(file_base, experiment):

    mcr_loc = 'matlab/mcr/v717/'
    
    command = 'sh ./run_run_crosscat.sh '
    command += mcr_loc + ' '
    command += in_folder + ' '
    command += file_base + ' '
    command += experiment + ' '
    command += n_chains + ' '
    command += n_pred_samples + ' '
    command += n_mcmc_iter
    out = os.popen(command).read()
    
    return out

def parse_out(experiment, out):
    if experiment is 'regression':
        out = out.split('#####')
        values = [0]*2
        values[0] = out[1]
        values[1] = out[3]
    if experiment is 'correlation':
        out = out.split('#####')
        values = [0]*(len(out)/2)
        for i in range(len(values)):
            values[i] = out[2*i - 1]
    return values

def run(file_base, experiment):
    id = cloud.call(run_matlab, 
                    file_base, 
                    experiment, 
                    _type='c2',
                    _env='matlab')
    return id


def run_ring(file_base):

    d = 2

    widths = np.array(range(1,10,2))/10.0
    true_percent_ent = [0]*len(widths)
    r_sq_vals = [0]*len(widths)

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('ring_width, rep, mutual_info\n')

    for i in range(len(widths)):
        
        w = widths[i]

        for j in range(hist_reps):
            
            if parse:
                f.write(str(w) + ',' + str(j) + ',' + h + '\n')
            else:
                name = file_base + '-width-' + str(w)
                id = run(name, 'correlation')
                f.write(str(w) + ',' + str(j) + ',' + str(id) + '\n')
        
    f.close()

def run_correlation(file_base):

    ns = [5, 10, 25, 50, 100]
    
    corrs = np.array(range(0,11))/10.0

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('n,correlation,rep,mutual_info\n')
    
    for j in range(len(ns)):
        for i in range(len(corrs)):
            
            n = ns[j]
            corr = corrs[i]

            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
                        
            for k in range(hist_reps):
                if parse:
                    f.write(','.join(map(str, [n,corr,k,id])) + '\n')
                else:
                    id = run(name, 'correlation')
                    f.write(str(n) + ',' + str(corr) + ',' + str(k) + ',' + str(id) + '\n')

    f.close()

def run_outliers(file_base):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('n,rep,mutual_info\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
            
        name = file_base + '-n-' + str(n)        

        for k in range(hist_reps):
            if parse:
                f.write(','.join(map(str, [n,k,h])) + '\n')
            else:
                id = run(name, 'correlation')
                f.write(','.join(map(str, [n,k,id])) + '\n')
                             
    f.close()

def run_outliers_correlated(file_base):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('n,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
        
        name = file_base + '-n-' + str(n)

        for k in range(hist_reps):
            if parse:
                f.write(','.join(map(str, [n,k,h])) + '\n')
            else:
                id = run(name, 'correlation')
                f.write(','.join(map(str, [n,k,id])) + '\n')

    f.close()

def run_correlated_pairs(file_base):

    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('n,corr,rep,mutual_info\n')

    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
            
            for k in range(hist_reps):
                if parse:
                    f.write(','.join(map(str, [n,corr,k,h])) + '\n')
                else:
                    id = run(name, 'correlation')
                    f.write(','.join(map(str, [n,corr,k,id])) + '\n')
                             
    f.close()

def run_correlated_halves(file_base):
    
    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('n,corr,rep,mutual_info\n')
    
    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
            
            for k in range(hist_reps):
                if parse:
                    f.write(','.join(map(str, [n,corr,k,h])) + '\n')
                else:
                    id = run(name, 'correlation')
                    f.write(','.join(map(str, [n,corr,k,id])) + '\n')

                             
    f.close()

def run_anova(file_base, n = 100, n_outliers = 0, 
              b1 = 1, b2 = 1, interaction = False,
              corr = 0, omit = False):

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        f.write('rep,cmi_xz,cmi_yz\n')

    name = file_base

    for k in range(hist_reps):
        if parse:
            f.write(','.join(map(str, [k, h1, h2])) + '\n')
        else:
            id = run(name, 'regression')
            f.write(','.join(map(str, [k, id])) + '\n')
                             
    f.close()

#if __name__ == "__main__":
if False:
    for i in range(data_reps):
        run_ring('ring-i-' + str(i))
        run_correlation('correlation-i-' + str(i))
        run_outliers('outliers-i-' + str(i))
        run_outliers_correlated('outliers-correlated-i-' + str(i))
        run_correlated_pairs('correlated-pairs-i-' + str(i))
        run_correlated_halves('correlated-halves-i-' + str(i))
        run_anova('simple-anova-i-' + str(i))
        run_anova('simple-anova-omitted-i-' + str(i), omit = True)
        run_anova('simple-anova-mixture-i-' + str(i), n = 50, n_outliers = 5)
        run_anova('anova-1-i-' + str(i), interaction = True)
        run_anova('anova-2-i-' + str(i), b2 = 0, interaction = True)
        run_anova('anova-3-i-' + str(i), b1 = 0, b2 = 0, interaction = True)
        run_anova('anova-1-omitted-i-' + str(i), interaction = True, omit = True)
        run_anova('anova-2-omitted-i-' + str(i), b2 = 0, interaction = True, omit = True)
        run_anova('anova-3-omitted-i-' + str(i), b1 = 0, b2 = 0, interaction = True,
                  omit = True)
        run_anova('anova-1-mixture-i-' + str(i), interaction = True, n = 50, n_outliers = 5)
        run_anova('anova-2-mixture-i-' + str(i), b2 = 0, interaction = True, n = 50, n_outliers = 5)
        run_anova('anova-3-mixture-i-' + str(i), b1 = 0, b2 = 0, interaction = True, n = 50, n_outliers = 5)
        
        corr = 0.999
        run_anova('anova-correlated-1-i-' + str(i), interaction = True, corr = corr)
        run_anova('anova-correlated-2-i-' + str(i), b2 = 0, interaction = True, 
                  corr = corr)
        run_anova('anova-correlated-3-i-' + str(i), b1 = 0, b2 = 0, interaction = True,
                  corr = corr)
        run_anova('anova-correlated-1-omitted-i-' + str(i), interaction = True, 
                  corr = corr, omit = True)
        run_anova('anova-correlated-2-omitted-i-' + str(i), b2 = 0, interaction = True, 
                  corr = corr, omit = True)
        run_anova('anova-correlated-3-omitted-i-' + str(i), b1 = 0, b2 = 0, 
                  interaction = True, corr = corr, omit = True)


