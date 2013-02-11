import cloud
import numpy as np
import math
import matplotlib.pyplot as plt

cloud.start_simulator()

out_folder = '../../crosscat-results/'

def run_ring(file_base, plot = False):

    d = 2

    widths = np.array(range(1,10,2))/10.0
    true_percent_ent = [0]*len(widths)
    r_sq_vals = [0]*len(widths)

    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('ring_width, mutual_info\n')

    for i in range(len(widths)):
        
        w = widths[i]
        
        cloud.files.put('../../data/' + file_base + '-width-' + str(w) + '-data.csv')
        cloud.files.put('../../data/' + file_base + '-width-' + str(w) + '-labels.csv')
        
        f.write(str(w) + ',' + str(true_percent_ent[i]) + ',' + str(lm.R2) + '\n')
        
    f.close()

def run_correlation(file_base, plot = False):

    ns = [5, 10, 25, 50, 100]
    
    corrs = np.array(range(0,11))/10.0

    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,correlation,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
        for i in range(len(corrs)):
            
            n = ns[j]
            corr = corrs[i]
            
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-data.csv')
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-labels.csv')
            
            f.write(','.join(map(str, [n,corr,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

def run_outliers(file_base, plot = False):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
            
        cloud.files.put('../../data/' + file_base + '-n-' + str(n) + '-data.csv')
        cloud.files.put('../../data/' + file_base + '-n-' + str(n) + '-labels.csv')
            
        f.write(','.join(map(str, [n,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

def run_outliers_correlated(file_base, plot = False):

    ns = [1, 5, 10, 25, 50]

    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
            
        cloud.files.put('../../data/' + file_base + '-n-' + str(n) + '-data.csv')
        cloud.files.put('../../data/' + file_base + '-n-' + str(n) + '-labels.csv')

    f.close()

def run_correlated_pairs(file_base, plot = False):

    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,corr,p,unadj_tp,unadj_fp,adj_tp,adj_fp\n')
    

    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-data.csv')
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-labels.csv')

            f.write(','.join(map(str, [n,corr,ps[m],utp,ufp,atp,afp])) + '\n')
                             
    f.close()

def run_correlated_halves(file_base, plot = False):
    
    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    
    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,corr,p,unadj_tp,unadj_fp,adj_tp,adj_fp\n')
    
    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-data.csv')
            cloud.files.put('../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr) + '-labels.csv')
            
            f.write(','.join(map(str, [n,corr,ps[m],utp,ufp,atp,afp])) + '\n')
                             
    f.close()

def run_anova(file_base, n = 100, n_outliers = 0, 
              b1 = 1, b2 = 1, interaction = False,
              corr = 0, omit = False):

    f = open(out_folder + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,beta2,beta12,p1,p2,p12,R_squared,F_pvalue\n')

    
    cloud.files.put('../../data/' + file_base + '-data.csv')
    cloud.files.put('../../data/' + file_base + '-labels.csv')

    f.write(','.join(map(str, [n,lm.b[0],lm.b[1],lm.b[2],lm.b[3],
                               lm.p[1], lm.p[2], lm.p[3],
                               lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

if __name__ == "__main__":

    data_reps = 5
    hist_reps = 50
    for i in range(data_reps):
        run_ring('ring-i-' + str(i))
        run_correlation('correlation-i-' + str(i))
        run_outliers('outliers-i-' + str(i))
        run_outliers_correlated('outliers-correlated-i-' + str(i))
        run_correlated_pairs('correlated_pairs-i-' + str(i))
        run_correlated_halves('correlated_halves-i-' + str(i))
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


