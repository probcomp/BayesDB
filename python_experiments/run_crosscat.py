import numpy as np

source('crosscat_helper.py')

data_offset = 1
data_reps = 2
hist_reps = 10
n_pred_samples = '250'
n_mcmc_iter = '500'

def run_ring(file_base):

    d = 2

    widths = np.array(range(1,10,2))/10.0
    true_percent_ent = [0]*len(widths)
    r_sq_vals = [0]*len(widths)
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('ring_width,rep,mutual_info\n')

    k = 0
    for i in range(len(widths)):
        
        w = widths[i]

        for j in range(hist_reps):
            
            if parse:
                job_id = int(job_ids[k])
                k += 1
                h = parse_out('correlation', job_id)[0].split(',')[2]
                f.write(str(w) + ',' + str(j) + ',' + h + '\n')
            else:
                name = file_base + '-width-' + str(w)
                job_id = run(name, 'correlation')
                f.write(str(w) + ',' + str(j) + ',' + str(job_id) + '\n')
        
    f.close()

def run_correlation(file_base):

    ns = [5, 10, 25, 50, 100]
    
    corrs = np.array(range(0,11))/10.0

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('n,correlation,rep,mutual_info\n')
    
    m = 0
    for j in range(len(ns)):
        for i in range(len(corrs)):
            
            n = ns[j]
            corr = corrs[i]

            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
                        
            for k in range(hist_reps):
                if parse:
                    job_id = int(job_ids[m])
                    m += 1
                    h = parse_out('correlation', job_id)[0].split(',')[2]
                    f.write(','.join(map(str, [n,corr,k,h])) + '\n')
                else:
                    job_id = run(name, 'correlation')
                    f.write(str(n) + ',' + str(corr) + ',' + str(k) + ',' + str(job_id) + '\n')

    f.close()

def run_outliers(file_base):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('n,rep,mutual_info\n')

    m = 0
    for j in range(len(ns)):
            
        n = ns[j]
            
        name = file_base + '-n-' + str(n)        

        for k in range(hist_reps):
            if parse:
                job_id = int(job_ids[m])
                m += 1
                h = parse_out('correlation', job_id)[0].split(',')[2]
                f.write(','.join(map(str, [n,k,h])) + '\n')
            else:
                job_id = run(name, 'correlation')
                f.write(','.join(map(str, [n,k,job_id])) + '\n')
                             
    f.close()

def run_outliers_correlated(file_base):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('n,beta0,beta1,R_squared,F_pvalue\n')

    m = 0
    for j in range(len(ns)):
            
        n = ns[j]
        
        name = file_base + '-n-' + str(n)

        for k in range(hist_reps):
            if parse:
                job_id = int(job_ids[m])
                m += 1
                h = parse_out('correlation', job_id)[0].split(',')[2]
                f.write(','.join(map(str, [n,k,h])) + '\n')
            else:
                job_id = run(name, 'correlation')
                f.write(','.join(map(str, [n,k,job_id])) + '\n')

    f.close()

def run_correlated_pairs(file_base):

    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('n,corr,rep,i,j,mutual_info\n')

    m = 0
    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
            
            for k in range(hist_reps):
                if parse:
                    job_id = int(job_ids[m])
                    m += 1
                    h = parse_out('correlation', job_id)
                    for l in range(len(h)):
                        f.write(','.join(map(str, [n,corr,k])) + ',' + h[l] + '\n')
                else:
                    job_id = run(name, 'correlation')
                    f.write(','.join(map(str, [n,corr,k,job_id])) + '\n')
                             
    f.close()

def run_correlated_halves(file_base):
    
    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('n,corr,rep,i,j,mutual_info\n')
    
    m = 0
    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            name = file_base + '-n-' + str(n) + '-corr-' + str(corr)
            
            for k in range(hist_reps):
                if parse:
                    job_id = int(job_ids[m])
                    m += 1
                    h = parse_out('correlation', job_id)
                    for l in range(len(h)):
                        f.write(','.join(map(str, [n,corr,k])) + ',' + h[l] + '\n')
                else:
                    job_id = run(name, 'correlation')
                    f.write(','.join(map(str, [n,corr,k,job_id])) + '\n')

                             
    f.close()

def run_anova(file_base, n = 100, n_outliers = 0, 
              b1 = 1, b2 = 1, interaction = False,
              corr = 0, omit = False):

    f = open(out_folder + file_base + '-results.csv', 'w')
    if parse:
        job_ids = get_job_ids(file_base)
        f.write('rep,mi_xz,mi_yz\n')

    name = file_base

    for k in range(hist_reps):
        if parse:
            job_id = int(job_ids[k])
            h = parse_out('regression', job_id)
            f.write(','.join(map(str, [k, h[0], h[1]])) + '\n')
        else:
            job_id = run(name, 'regression')
            f.write(','.join(map(str, [k, job_id])) + '\n')
                             
    f.close()

for i in range(data_offset, data_offset + data_reps):

    run_ring('ring-i-' + str(i))
    run_correlation('correlation-i-' + str(i))
    run_outliers('outliers-i-' + str(i))
    run_outliers_correlated('outliers-correlated-i-' + str(i))
    run_correlated_pairs('correlated-pairs-i-' + str(i))
    run_correlated_halves('correlated-halves-i-' + str(i))

    run_anova('simple-anova-i-' + str(i))
    run_anova('simple-anova-omitted-i-' + str(i), omit = True)
    #run_anova('simple-anova-mixture-i-' + str(i), n = 50, n_outliers = 5)
    run_anova('anova-1-i-' + str(i), interaction = True)
    run_anova('anova-2-i-' + str(i), b2 = 0, interaction = True)
    run_anova('anova-3-i-' + str(i), b1 = 0, b2 = 0, interaction = True)
    run_anova('anova-1-omitted-i-' + str(i), interaction = True, omit = True)
    run_anova('anova-2-omitted-i-' + str(i), b2 = 0, interaction = True, omit = True)
    run_anova('anova-3-omitted-i-' + str(i), b1 = 0, b2 = 0, interaction = True,
              omit = True)
    #run_anova('anova-1-mixture-i-' + str(i), interaction = True, n = 50, n_outliers = 5)
    #run_anova('anova-2-mixture-i-' + str(i), b2 = 0, interaction = True, n = 50, n_outliers = 5)
    #run_anova('anova-3-mixture-i-' + str(i), b1 = 0, b2 = 0, interaction = True, n = 50, n_outliers = 5)
    
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
