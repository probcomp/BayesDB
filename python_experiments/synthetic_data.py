import random
import math
import matplotlib.pyplot as plt

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

def sd_increasing(s):
    return sum(map(lambda x: (x + 1.0)/(2*d), s))
def sd_constant(s):
    return 0.1

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
            samples[i][j + 1] = y + random.random()*(p - y)
        else:       
            samples[i][j + 1] = y + random.gauss(0, sd_func(samples[i][0:p]))

    return samples

def random_regression_pairs(n, pairs):
    
    d = pairs * 2
    samples = [[0]*(d + 1) for i in range(n)]

    for i in range(pairs):
        next = random_regression(n)
        for j in range(n):
            samples[j][(2*i):(2*i + 1)] = next[j]
    
    return samples

#samples = random_regression_pairs(1000,3)
#m = zip(*samples)
#plt.plot(m[0],m[4], 'r.')
#plt.show()

    

