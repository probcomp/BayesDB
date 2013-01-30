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

d = 2

widths = np.array(range(1,10))/10.0
true_perc_ent = [0]*len(widths)
r_sq_vals = [0]*len(widths)

for i in range(len(widths)):

    w = widths[i]

    data = np.array(synth.random_ring(1000, d, w))

    pdf = lambda x, y: ring_pdf(x, y, 1 - w)
    c_pdf = lambda x, y: ring_cond_pdf(x, y, 1 - w)
    ce = cond_entropy(data[:,0], data[:,1], c_pdf)
    me = entropy(data[:,1], data[:,1], pdf, c_pdf)
    true_perc_ent[i] = ce/me

    lm = ols.ols(data[:,0], data[:,1:], 'y', 
                 map(lambda x: 'x' + str(x), range(d - 1)))

    r_sq_vals[i] = lm.R2

plt.plot(true_perc_ent, r_sq_vals)
plt.show()
