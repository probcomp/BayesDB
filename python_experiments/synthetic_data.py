import random
import math
import matplotlib.pyplot as plt
import numpy as np

# TODO: test!!! especially that width is what you think it is!
def random_ring(n, d, width):
    
    scale = 1.0/(1 - (1 - width)**d)
    
    samples = [[0]*d for i in range(n)]
    
    for i in range(n):
        
        for j in range(d):
            samples[i][j] = random.gauss(0,1)
            
        r = math.sqrt(sum(map(lambda x: x**2, samples[i])))
        u = (1.0 - random.random()/scale)**(1.0/d)
        samples[i] = map(lambda x: u * 1/r * x, samples[i])
    
    return samples

def sd_increasing(value):
    return sum(map(lambda x: (x + 1.0)/(2*d), value))
def sd_constant(value, sd = 0.1):
    return sd

def random_regression(n, d = 1, 
                      outliers = 0, 
                      distractors = 0, 
                      sd_func = sd_constant):

    samples = [[0]*(d + 1) for i in range(n)]

    p = d - distractors

    for i in range(n):
        
        for j in range(d):
            samples[i][j] = random.random()*2 - 1
        
        y = sum(samples[i][0:p])
        if random.random() < outliers:
            samples[i][j + 1] = 100*p*random.random() - 50*p
        else:       
            samples[i][j + 1] = y + random.gauss(0, sd_func(samples[i][0:p]))

    return samples

def random_regression_pairs(n, pairs, sd_func):
    
    d = pairs * 2
    samples = [[0]*(d + 1) for i in range(n)]

    for i in range(pairs):
        next = random_regression(n, sd_func = sd_func)
        for j in range(n):
            samples[j][(2*i):(2*i + 1)] = next[j]
    
    return samples

def correlated_data(n, corr, dim = 2):
    mean = [0]*dim
    cov = [[corr]*dim for i in range(dim)]
    for i in range(dim):
        cov[i][i] = 1
    samples = np.random.multivariate_normal(mean, cov, n)
    return samples

def correlated_pairs(n, pairs, corr):
    
    d = pairs*2
    samples = [[0]*(d + 1) for i in range(n)]

    for i in range(pairs):
        next = correlated_data(n, corr)
        for j in range(n):
            samples[j][(2*i):(2*i + 1)] = next[j]
    
    return samples

def correlated_halves(n, group_size, corr):
    
    first = correlated_data(n, corr, group_size)
    second = correlated_data(n, corr, group_size)
    samples = np.hstack([first, second])
    
    return samples

def outlier_data(n):
    cov = [[1,0], [0,1]]
    samples = np.random.multivariate_normal([0,0],cov,50)
    outliers = np.random.multivariate_normal([7,7],cov,n)
    samples = np.vstack([samples, outliers])
    return samples

def outlier_correlated_data(n):
    cov = [[1,0.8], [0.8,1]]
    samples = np.random.multivariate_normal([0,0],cov,50)
    cov = [[1,0], [0,1]]
    outliers = np.random.multivariate_normal([-3.5,3.5],cov,n)
    samples = np.vstack([samples, outliers])
    return samples

def regression_data(n, corr = 0, omit = False):
    samples = np.zeros((n, 3))
    samples[:,0:2] = correlated_data(n, corr)
    samples[:,2] = samples[:,0] + samples[:,1]
    if omit:
        samples[:,1] = np.random.normal(0, 1, n)
    return samples

def write_data(samples, file_base):
    
    f = open(file_base + '-data.csv', 'w')
    for i in range(len(samples)):
        for j in range(len(samples[i]) - 1):
            f.write(str(samples[i][j]) + ',')
        f.write(str(samples[i][j + 1]) + '\n')
    f.close()
    
    f = open(file_base + '-labels.csv', 'w')
    for i in range(len(samples[0]) - 1):
            f.write('normal_inverse_gamma,')
    f.write('normal_inverse_gamma')
    f.close()

#samples = random_regression_pairs(1000,3)
#m = zip(*samples)
#plt.plot(m[0],m[4], 'r.')
#plt.show()

    

