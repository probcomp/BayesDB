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
def run_ring(plot = False):

    d = 2

    widths = np.array(range(1,10,2))/10.0
    true_percent_ent = [0]*len(widths)
    r_sq_vals = [0]*len(widths)

    f = open('../../results/ring-results.csv', 'w')
    f.write('ring_width, percent_entropy, R_squared\n')

    for i in range(len(widths)):
        
        w = widths[i]
        
        data = synth.random_ring(1000, d, w)
        synth.write_data(data, '../../data/ring-width-' + str(w))
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

# TODO: should we vary the sd or the true beta1?
def run_simple_regression(plot = False):
    
    ns = [10, 50, 100]
    
    sds = [0.1, 0.4, 0.8, 2] 
    
    f = open('../../results/regression-results.csv', 'w')
    f.write('n,standard_deviation,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
        for i in range(len(sds)):
            
            n = ns[j]
            sd = sds[i]
            
            data = synth.random_regression(n, 1, sd_func = lambda x: sd)
            synth.write_data(data, '../../data/regression-n-' +
                             str(n) + '-sd-' + str(sd))
            data = np.array(data)
            
            lm = ols.ols(data[:,1], data[:,0], 'y', ['x0'])
            
            f.write(','.join(map(str, [n,sd,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

    if plot:
        y = lm.b[0] + data[:,0]*lm.b[1]
        plt.plot(data[:,0], data[:,1], '.', data[:,0], y, 'r')
        plt.show()

def run_outlier_regression(plot = False):
    
    ns = [10, 50, 100]
    
    sds = [0.1, 0.4, 0.8, 2] 
    
    f = open('../../results/outlier-regression-results.csv', 'w')
    f.write('n,standard_deviation,beta0,beta1,R_squared,F_pvalue\n')
    
    for j in range(len(ns)):
        for i in range(len(sds)):
            
            n = ns[j]
            sd = sds[i]
            
            data = synth.random_regression(n, 1, 
                                           outliers = 0.1,
                                           sd_func = lambda x: sd)
            synth.write_data(data, '../../data/outlier-regression-n-' +
                             str(n) + '-sd-' + str(sd))
            data = np.array(data)
            
            lm = ols.ols(data[:,1], data[:,0], 'y', ['x0'])
            
            f.write(','.join(map(str, [n,sd,lm.b[0],lm.b[1],lm.R2,lm.Fpv])) + '\n')
                             
    f.close()

    if plot:
        y = lm.b[0] + data[:,0]*lm.b[1]
        plt.plot(data[:,0], data[:,1], '.', data[:,0], y, 'r', data[:,0], data[:,0])
        plt.show()

def run_pairwise_regressions(plot = False):
    
    n = 50

    nums_pairs = [2, 5, 10]    
    sds = [0.1, 2]
    ps = [0.001, 0.01, 0.025, 0.05, 0.10]
    
    f = open('../../results/pairwise-regression-results.csv', 'w')
    f.write('pairs,standard_deviation,p,unadj_tp,unadj_fp,adj_tp,adj_fp\n')
    
    adj_tp = [[[0]*len(ps) for i in range(len(sds))] for j in range(len(nums_pairs))]
    adj_fp = [[[0]*len(ps) for i in range(len(sds))] for j in range(len(nums_pairs))]
    unadj_tp = [[[0]*len(ps) for i in range(len(sds))] for j in range(len(nums_pairs))]
    unadj_fp = [[[0]*len(ps) for i in range(len(sds))] for j in range(len(nums_pairs))]

    for i in range(len(nums_pairs)):
        for j in range(len(sds)):
            
            pairs = nums_pairs[i]
            sd = sds[j]
            
            data = synth.random_regression_pairs(n, pairs,
                                           sd_func = lambda x: sd)
            synth.write_data(data, '../../data/pairwise-regression-pairs-' +
                             str(pairs) + '-sd-' + str(sd))
            data = np.array(data)                

            for k in range(0, 2*pairs - 1):
                for l in range(k + 1, 2*pairs):

                    lm = ols.ols(data[:,l], data[:,k], 'y', ['x0'])
                    
                    for m in range(len(ps)):

                        alpha = ps[m]
                        bonferroni = ps[m]/(pairs * (pairs - 1) / 2)

                        unadj_tp[i][j][m] += (l == k + 1) and (lm.Fpv < alpha)
                        unadj_fp[i][j][m] += (l != k + 1) and (lm.Fpv < alpha)
                        adj_tp[i][j][m] += (l == k + 1) and (lm.Fpv < bonferroni)
                        adj_fp[i][j][m] += (l != k + 1) and (lm.Fpv < bonferroni)

            for m in range(len(ps)):
                utp = unadj_tp[i][j][m]
                ufp = unadj_fp[i][j][m]
                atp = adj_tp[i][j][m]
                afp = adj_fp[i][j][m]
                f.write(','.join(map(str, [pairs,sd,ps[m],utp,ufp,atp,afp])) + '\n')
                             
    f.close()

    if plot:
        plt.plot(adj_tp[2][1], adj_fp[2][1], '-', 
                 unadj_tp[2][1], unadj_fp[2][1])
        plt.show()

if __name__ == "__main__":

    run_ring()
    run_simple_regression()
    run_outlier_regression()
    run_pairwise_regressions()
