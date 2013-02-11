import ols
import synthetic_data as synth
import numpy as np
import math
import matplotlib.pyplot as plt

# TODO: test!!! and generalize to higher dimensions
def ring_seg_area(x, r):
    return 2*(math.sqrt(1 - x**2) - math.sqrt(max(r**2 - x**2, 0)))

def ring_cond_pdf(x, y, r):
    return 1.0/ring_seg_area(y, r)

# TODO: generalize to higher dimensions
def ring_area(r):
    return math.pi - math.pi * r**2

def ring_pdf(x, y, r):
    return 1.0/ring_area(r)

# TODO: test!!! compare to conditional calculateion
#def entropy(x_vec, pdf):
#    return sum(map(lambda x: -math.log(pdf(x)), x_vec))/len(x_vec)

def entropy(x_vec, y_vec, joint_pdf, cond_pdf):
    je = joint_entropy(x_vec, y_vec, joint_pdf)
    ce = cond_entropy(y_vec, x_vec, cond_pdf)
    return je - ce

def joint_entropy(x_vec, y_vec, pdf):
    n = len(x_vec)
    return sum(map(lambda x, y: -math.log(pdf(x, y)), x_vec, y_vec))/n

# TODO: test!! compare to computation with conditional distributions
#def conditional_entropy(y_vec, x_vec, joint_pdf, pdf_x):
#    return joint_entropy(x_vec, y_vec, joint_pdf) - entropy(x_vec, pdf_x)

def cond_entropy(x_vec, y_vec, cond_pdf):
    return joint_entropy(x_vec, y_vec, cond_pdf)

# TODO: clean up this function (make filenames, widths, etc. parameters)
def run_ring(file_base, plot = False):

    d = 2

    widths = np.array(range(1,10,2))/10.0
    true_percent_ent = [0]*len(widths)
    r_sq_vals = [0]*len(widths)

    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('ring_width, percent_entropy, R_squared\n')

    for i in range(len(widths)):
        
        w = widths[i]
        
        data = synth.random_ring(200, d, w)
        synth.write_data(data, '../../data/' + file_base + '-width-' + str(w))
        data = np.array(data)
        
        pdf = lambda x, y: ring_pdf(x, y, 1 - w)
        c_pdf = lambda x, y: ring_cond_pdf(x, y, 1 - w)
        ce = cond_entropy(data[:,0], data[:,1], c_pdf)
        me = entropy(data[:,1], data[:,1], pdf, c_pdf)
        true_percent_ent[i] = ce/me
        
        lm = ols.ols(data[:,0], data[:,1:], 'y', 
                     map(lambda x: 'x' + str(x), range(d - 1)))
        
        r_sq_vals[i] = lm.R2
        
        f.write(str(w) + ',' + str(true_percent_ent[i]) + ',' + str(lm.R2) + '\n')
        
    f.close()

    if plot:
        plt.plot(true_percent_ent, r_sq_vals)
        plt.show()

def run_correlation(file_base, plot = False):

    ns = [5, 10, 25, 50, 100]
    
    corrs = np.array(range(0,11))/10.0

    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,correlation,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
        for i in range(len(corrs)):
            
            n = ns[j]
            corr = corrs[i]
            
            data = synth.correlated_data(n, corr)
            synth.write_data(data, '../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr))
            data = np.array(data)
            
            lm = ols.ols(data[:,1], data[:,0], 'y', ['x0'])
            
            f.write(','.join(map(str, [n,corr,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

    if plot:
        y = lm.b[0] + data[:,0]*lm.b[1]
        plt.plot(data[:,0], data[:,1], '.', data[:,0], y, 'r')
        plt.show()    

def run_outliers(file_base, plot = False):

    ns = [1, 5, 10, 25, 50]

    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
            
        data = synth.outlier_data(n)
        synth.write_data(data, '../../data/' + file_base + '-n-' + str(n))
        data = np.array(data)
        
        lm = ols.ols(data[:,1], data[:,0], 'y', ['x0'])
            
        f.write(','.join(map(str, [n,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

    if plot:
        y = lm.b[0] + data[:,0]*lm.b[1]
        plt.plot(data[:,0], data[:,1], '.', data[:,0], y, 'r')
        plt.show()    

def run_outliers_correlated(file_base, plot = False):

    ns = [1, 5, 10, 25, 50]

    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
            
        n = ns[j]
            
        data = synth.outlier_correlated_data(n)
        synth.write_data(data, '../../data/' + file_base + '-n-' + str(n))
        data = np.array(data)
        
        lm = ols.ols(data[:,1], data[:,0], 'y', ['x0'])
            
        f.write(','.join(map(str, [n,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

    if plot:
        y = lm.b[0] + data[:,0]*lm.b[1]
        plt.plot(data[:,0], data[:,1], '.', data[:,0], y, 'r')
        plt.show()    

def run_correlated_pairs(file_base, plot = False):
    
    pairs = 25
    ncols = 2*pairs

    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    ps = [0.0, 0.0001, 0.001, 0.01, 0.025, 0.05, 0.10, 0.2, 0.5, 1]
    
    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,corr,p,unadj_tp,unadj_fp,adj_tp,adj_fp\n')
    
    adj_tp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    adj_fp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    unadj_tp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    unadj_fp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]

    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            data = synth.correlated_pairs(n, pairs, corr)
            synth.write_data(data, '../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr))
            data = np.array(data)                

            for k in range(0, ncols - 1):
                for l in range(k + 1, ncols):

                    lm = ols.ols(data[:,l], data[:,k], 'y', ['x0'])
                    
                    for m in range(len(ps)):

                        alpha = ps[m]
                        bonferroni = ps[m]/(ncols * (ncols - 1) / 2)

                        unadj_tp[i][j][m] += (k % 2 == 0) and (l == k + 1) and (lm.Fpv < alpha)
                        unadj_fp[i][j][m] += ( (k % 2 == 1) or (l != k + 1) ) and (lm.Fpv < alpha)
                        adj_tp[i][j][m] += (k % 2 == 0) and (l == k + 1) and (lm.Fpv < bonferroni)
                        adj_fp[i][j][m] += ( (k % 2 == 1) or (l != k + 1) ) and (lm.Fpv < bonferroni)

            for m in range(len(ps)):
                utp = unadj_tp[i][j][m]
                ufp = unadj_fp[i][j][m]
                atp = adj_tp[i][j][m]
                afp = adj_fp[i][j][m]
                f.write(','.join(map(str, [n,corr,ps[m],utp,ufp,atp,afp])) + '\n')
                             
    f.close()

    if plot:
        plt.plot(adj_tp[2][1], adj_fp[2][1], '-', 
                 unadj_tp[2][1], unadj_fp[2][1])
        plt.show()


def run_correlated_halves(file_base, plot = False):
    
    group_size = 25
    ncols = group_size*2

    ns = [5, 25, 50, 100, 200]    
    corrs = np.array(range(0,11))/10.0
    ps = [0.0, 0.0001, 0.001, 0.01, 0.025, 0.05, 0.10, 0.2, 0.5, 1]
    
    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,corr,p,unadj_tp,unadj_fp,adj_tp,adj_fp\n')
    
    adj_tp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    adj_fp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    unadj_tp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]
    unadj_fp = [[[0]*len(ps) for i in range(len(corrs))] for j in range(len(ns))]

    for i in range(len(ns)):
        for j in range(len(corrs)):
            
            n = ns[i]
            corr = corrs[j]
            
            data = synth.correlated_halves(n, group_size, corr)
            synth.write_data(data, '../../data/' + file_base + '-n-' +
                             str(n) + '-corr-' + str(corr))
            data = np.array(data)                

            for k in range(0, ncols - 1):
                for l in range(k + 1, ncols):

                    lm = ols.ols(data[:,l], data[:,k], 'y', ['x0'])
                    
                    for m in range(len(ps)):

                        alpha = ps[m]
                        bonferroni = ps[m]/(ncols * (ncols - 1) / 2)

                        unadj_tp[i][j][m] += ((l < 25) == (k < 25)) and (lm.Fpv < alpha)
                        unadj_fp[i][j][m] += ((l < 25) != (k < 25)) and (lm.Fpv < alpha)
                        adj_tp[i][j][m] += ((l < 25) == (k < 25)) and (lm.Fpv < bonferroni)
                        adj_fp[i][j][m] += ((l < 25) != (k < 25)) and (lm.Fpv < bonferroni)

            for m in range(len(ps)):
                utp = unadj_tp[i][j][m]
                ufp = unadj_fp[i][j][m]
                atp = adj_tp[i][j][m]
                afp = adj_fp[i][j][m]
                f.write(','.join(map(str, [n,corr,ps[m],utp,ufp,atp,afp])) + '\n')
                             
    f.close()

    if plot:
        plt.plot(adj_tp[2][1], adj_fp[2][1], '-', 
                 unadj_tp[2][1], unadj_fp[2][1])
        plt.show()


def run_anova(file_base, n = 100, n_outliers = 0, 
              b1 = 1, b2 = 1, interaction = False,
              corr = 0, omit = False):

    f = open('../../results/' + file_base + '-results.csv', 'w')
    f.write('n,beta0,beta1,beta2,beta12,p1,p2,p12,R_squared,F_pvalue\n')

    data = synth.regression_data(n, b1, b2, interaction, corr, omit,
                                 n_outliers = n_outliers)
    synth.write_data(data, '../../data/' + file_base)
    x = np.zeros((n + n_outliers, 3))
    x[:,0:2] = data[:,0:2]
    x[:,2] = data[:,0]*data[:,1]
    y = data[:,2]
    
    lm = ols.ols(y, x, 'y', ['x0', 'x1', 'x1*x2'])
            
    f.write(','.join(map(str, [n,lm.b[0],lm.b[1],lm.b[2],lm.b[3],
                               lm.p[1], lm.p[2], lm.p[3],
                               lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

if __name__ == "__main__":

    reps = 5
    for i in range(reps):
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


