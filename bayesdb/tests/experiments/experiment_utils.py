#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import matplotlib
matplotlib.use('Agg')

import crosscat.tests.quality_tests.synthetic_data_generator as sdg
import crosscat.tests.component_model_extensions.ContinuousComponentModel as ccm
import random
import math
import time
import csv
import os
import pylab
import numpy
import copy
import pickle
from scipy.misc import logsumexp
from matplotlib.ticker import MaxNLocator

# imput a mode, get a BayesDB config string
config_map = {
    'cc'  : '',
    'crp' : 'WITH CONFIG crp mixture', 
    'nb'  : 'WITH CONFIG naive bayes'
}

def parser_args_to_dict(args):
    """
    converts argparse.ArgumentParser() args do a dict
    EX:
    >>> parser = argparse.ArgumentParser()
    >>> parser.add_argument('--num_rows', default=100, type=int) 
    >>> args = parser.parse_args()
    >>> parser_args_to_dict(args)
    {'num_rows': 100}
    """
    argsdict = vars(args)
    argsdict['time'] = int(time.time())
    return argsdict

def make_folder(path):
    """ builds a directory if one does not exist"""
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def csv_to_list(filename):
    """reads the csv filename into a list of lists"""
    T = []
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in reader:
            T.append(row)

    return T

def list_to_csv(filename, T):
    """writes the list of list T to csv filename"""
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in T:
            writer.writerow(row)

def gen_missing_data_csv(filename, prop_missing, exclude_cols=[], retex=False):
    """ 
    Generates a csv from the original but with missing data.

    Arguments:
    --filename: string. the filename of the origianl csv
    --prop_missing: float. the proportion of data to remove, [0,1]

    Keyword arguments:
    --exclude_cols: list of ints. Indices of columns to exclude in removal
    --retex: bool. If true, returns a dict with the keys:
    ---['table_missing']: numpy array of the data with removed values
    ---['table_filled']: numpy array of the data before removing values
    ---['column_names']: list of string of the column names 

    Returns (tuple):
    -- new_filename: string, the filename of the new .csv
    -- indices: list of lists of ints. First list is row indices, seconds is 
    column indices
    -- column_names: list of t strings. each column name

    Example:
    >>> filename = dha_no_strings.csv # can't load data with strings to numpy
    >>> exclude_cols = [0] # do not remove row IDs
    >>> new_filename, indices = gen_missing_data_csv(filename, .1, exclude_columns)
    """
    # read the header
    with open(filename, 'r') as f:
      csv_header = f.readline()
    csv_header = csv_header.rstrip()
    column_names = csv_header.split(',')
    column_names[-1] = column_names[-1].strip()

    # read in the data sans header
    T_filled = csv_to_list(filename)

    num_rows = len(T_filled)
    num_cols = len(T_filled[0])

    # get the column indices to remove
    col_indices = [c for c in range(num_cols) if c not in exclude_cols]
    row_indices = range(1, num_rows) # exclude header

    N = len(row_indices)*len(col_indices)

    # get the number of entries to remove (do not remove column 1)
    N_to_remove_per_col = int(N*prop_missing/len(col_indices))

    # get random indices
    unf_indices = []
    for col in col_indices:
        indices = [ (r,col) for r in row_indices]
        unf_indices_col = random.sample(indices, N_to_remove_per_col)
        unf_indices.extend(unf_indices_col)

    T_missing = copy.deepcopy(T_filled)

    # add missing values
    for index in unf_indices:
        T_missing[index[0]][index[1]] = 'nan'
    
    # format the indices so they can be used in a numpy array
    indices = [[idx[0]-1 for idx in unf_indices], [idx[1] for idx in unf_indices]]

    filename, fileExtension = os.path.splitext(filename)
    
    # save the file (with header)
    new_filename = filename + '_missing_exp.csv'

    # write the new file
    list_to_csv(new_filename, T_missing)

    if retex:
        # convert table minus header to numpy array
        array_filled = []
        array_missing = []
        for row in range(1, num_rows):
            array_filled.append([float(v) for v in T_filled[row]])
            array_missing.append([float(v) for v in T_missing[row]])
        extra = { 
            'array_missing' : numpy.array(array_missing), 
            'array_filled' : numpy.array(array_filled), 
            'column_names': column_names}
        return new_filename, indices, column_names, extra
    else:
        return new_filename, indices, column_names

def column_average_array(X, exclude_cols=[]):
    """
    Returns a tiled array of column averages (does not average missing values)
    if exclude_cols is not empty, leaves a zeros for those columns

    Example:
    >>> A = numpy.random.randint(5,size=(5,5))
    >>> A = numpy.array(A,dtype=float)
    >>> A[numpy.nonzero(A==1)] = float('NaN')
    >>> A
    array([[ 4., 0., 2.,  2., nan],
           [ 0., 2., 0.,  3., nan],
           [ 2., 0., 0.,  0.,  4.],
           [ 3., 0., 4.,  0.,  3.],
           [ 3., 3., 0., nan,  0.]])
    >>> B = eu.column_average_array(A, exclude_cols=[0])
    >>> B
    array([[ 0., 1., 1.2, 1.25, 2.33333333],
           [ 0., 1., 1.2, 1.25, 2.33333333],
           [ 0., 1., 1.2, 1.25, 2.33333333],
           [ 0., 1., 1.2, 1.25, 2.33333333],
           [ 0., 1., 1.2, 1.25, 2.33333333]])
    """

    n_rows, n_cols = X.shape
    cols = [c for c in range(n_cols) if c not in exclude_cols]

    counts = numpy.zeros(n_cols)
    sums = numpy.zeros(n_cols)
    aves = numpy.zeros(n_cols)
    for col in cols:
        for row in range(n_rows):
            if not numpy.isnan(X[row, col]):
                counts[col] += 1.0
                sums[col] += X[row, col]

        aves[col] = sums[col]/counts[col]

    Y = numpy.tile(aves, (n_rows, 1))

    return Y

def gen_held_out_data(filename, new_filename, num_rows):
    """
    Removes the bottom num_rows rows of the csv, filename and save a new csv to
    new_filename
    """

    # read the header
    with open(filename, 'r') as f:
      csv_header = f.readline()
    csv_header = csv_header.rstrip()
    
    # read in the data sans header
    X = numpy.genfromtxt(filename, delimiter=',', skip_header=1)

    # remove the bottom rows
    Y = numpy.array(X[0:-num_rows,:])

    # save the file
    numpy.savetxt(new_filename, Y, delimiter=',', header=csv_header, comments='')

    return Y

def get_true_logp(x, col, structure):
    """
    Currently only supports continuous.
    Returns logp of x in [row,col] under structure
    """
    # get the cluster parameters
    view = structure['cols_to_views'][col]
    weights = structure['cluster_weights'][view]

    logps = []
    for params, weight in zip(structure['component_params'][col], weights):
        logp = math.log(weight) + ccm.p_ContinuousComponentModel.log_pdf(x, params)[0]
        logps.append(logp)

    return logsumexp(logps)


def gen_data(filename, arsgin, save_csv=True):
    """
        Generates a synthetic tablel with given properties. For full 
        documentation see sdg.gen_data
    """
    cctypes = arsgin['cctypes']
    n_rows = arsgin['num_rows']
    n_cols = arsgin['num_cols']
    n_views = arsgin['num_views']
    n_clusters = arsgin['num_clusters']
    separation = arsgin['separation']
    seed = arsgin['seed']

    if 'distargs' in arsgin.keys():
        distargs = arsgin['distargs']
    else:
        distargs = None

    random.seed(seed)

    # need to generate cluster_weights and cols_to_views
    cols_to_views = range(n_views)
    for c in range(n_views, n_cols):
        cols_to_views.append(random.randrange(n_views))

    cluster_weights = []
    for v in range(n_views):
        cluster_weights.append([1./n_clusters]*n_clusters)

    T, _, structure = sdg.gen_data(cctypes, n_rows, cols_to_views, 
                        cluster_weights, separation,
                        seed=seed, distargs=distargs, return_structure=True)

    T = numpy.array(T)

    if save_csv:
        header = [ 'col_'+str(col) for col in range(n_cols) ]

        # write the data to a list of list
        out = [header]
        for row in range(n_rows):
            row_out = []
            for col in range(n_cols):
                if cctypes[col] == 'continuous':
                    value = T[row][col]
                elif cctypes[col] == 'multinomial':
                    value = int(T[row][col])
                else:
                    raise ValueError("unsupported cctype: %s" % cctypes[col])
                row_out.append(value)
            out.append(row_out)

        list_to_csv(filename, out)

    return T, structure

def generate_noise(mode, num_rows, num_cols, multinomial_categories=5):
    """
    Generates a table of random noise
    Inputs:
    -- mode: (string) type of data to sample. 
    ---- 'continuous': only continuous data columns
    ---- 'multinomial': only multinomial data columns
    ---- 'mixed': both continuous and multinomial data columns in even proportion
    -- num_rows: (int) the number of rows
    -- num_cols: (int) the number of columns
    -- multinomial_categories: (int) number of categories for multinomial data
    Outputs:
    -- T: (list of lists of data)
    -- col_types: (list of strings) the data type of each column
    """
    cctypes = ['continuous','multinomial']
    if mode == 'mixed':
        col_types = [random.choice(cctypes) for _ in range(num_cols)]
    elif mode == 'continuous':
        col_types = ['continuous']*num_cols
    elif mode == 'multinomial':
        col_types = ['multinomial']*num_cols
    else:
        raise ValueError("Invalid mode: %s" % mode)
    
    T = []
    for row in range(num_rows):
        row_data = []
        for col in range(num_cols):
            if col_types[col] == 'continuous':
                row_data.append(random.gauss(0,1))
            elif col_types[col] == 'multinomial':
                row_data.append(random.randrange(multinomial_categories))
            else:
                raise ValueError("Invalid type: %s" % col_types[col])
        T.append(row_data)
    return T, col_types

def get_column_types(data_mode, num_cols, multinomial_categories=5):
    cctypes = ['continuous','multinomial']
    if data_mode == 'mixed':
        col_types = [random.choice(cctypes) for _ in range(num_cols)]
        distargs = []
        for col in range(num_cols):
            if col_types[col] == 'multinomial':
                distargs.append({'K':multinomial_categories})
            else:
                distargs.append(None)

    elif data_mode == 'continuous':
        col_types = ['continuous']*num_cols
        distargs = [None]*num_cols

    elif data_mode == 'multinomial':
        col_types = ['multinomial']*num_cols
        distargs = [{'K':multinomial_categories}]*num_cols

    else:
        raise ValueError("Invalid data_mode: %s" % data_mode)

    return col_types, distargs

# shape data
# `````````````````````````````````````````````````````````````````````````````
def gen_sine_wave(N, noise=.5):
    x_range = [-3.0*math.pi/2.0, 3.0*math.pi/2.0]
    X = numpy.zeros( (N,2) )
    for i in range(N):
        x = random.uniform(x_range[0], x_range[1])
        y = math.cos(x)+random.random()*(-random.uniform(-noise, noise));
        X[i,0] = x
        X[i,1] = y

    # scale
    X += math.fabs(numpy.min(X))
    X /= numpy.max(X)
    X *= math.pi

    return X

def gen_x(N, rho=.95):
    X = numpy.zeros( (N,2) )
    for i in range(N):
        if random.random() < .5:
            sigma = numpy.array([[1,rho],[rho,1]])
        else:
            sigma = numpy.array([[1,-rho],[-rho,1]]);

        x = numpy.random.multivariate_normal([0,0],sigma)
        X[i,:] = x;

    # scale
    X += math.fabs(numpy.min(X))
    X /= numpy.max(X)
    X *= math.pi

    return X

def gen_ring(N, width=.2):
    X = numpy.zeros((N,2))
    for i in range(N):
        angle = random.uniform(0.0,2.0*math.pi)
        distance = random.uniform(1.0-width,1.0)
        X[i,0] = math.cos(angle)*distance+math.pi
        X[i,1] = math.sin(angle)*distance+math.pi

    return X

        
def gen_four_dots(N=200, stddev=.25):
    X = numpy.zeros((N,2))
    mx = [ 1, 3, 1, 3]
    my = [ 1, 1, 3, 3]
    for i in range(N):
        n = random.randrange(4)
        x = random.normalvariate(mx[n], stddev)
        y = random.normalvariate(my[n], stddev)
        X[i,0] = x
        X[i,1] = y

    return X
# plotting tests
# `````````````````````````````````````````````````````````````````````````````
def plot_error_bars_shrink(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    pylab.locator_params(nbins=3)
    fig = pylab.figure(num=None, figsize=(8,10), facecolor='w', edgecolor='k')

    num_queries = result['num_queries']
    confidence = result['config']['confidence']

    dep_means = result['dependence_probability_mean'] 
    dep_error = result['dependence_probability_error']
    inf_means = result['infer_means']
    inf_error = result['infer_stderr']
    x = result['iteration']

    ax = pylab.subplot(3,1,1)
    for q in range(num_queries):
        pylab.errorbar(x, dep_means[q,:], yerr=dep_error[q,:], alpha=.7)
    pylab.title('Dependence probability')
    ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.xaxis.set_major_locator(MaxNLocator(5))
    pylab.xlabel('iteration')

    ax = pylab.subplot(3,1,2)
    for q in range(num_queries):
        pylab.errorbar(x, inf_means[q,:], yerr=inf_error[q,:], alpha=.7)
    pylab.title('Infer. Confidence=%1.2f' % confidence)
    pylab.xlabel('iteration')
    ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.xaxis.set_major_locator(MaxNLocator(5))

    num_iters = result['config']['num_iters']
    num_chains = result['config']['num_chains']
    num_runs = result['config']['num_runs']
    prop_missing = result['config']['prop_missing']
    confidence = result['config']['confidence']

    txt = '''
        Left: Dependence probability with standard error calculated over %i runs of %i 
        chains for %i iterations.

        Right: Proportion of missing data successfully imputed with INFER with %1.2f
        confidence.

        Data used was dha.csv. %1.2f percent of data was removed.
    ''' % (num_runs, num_chains, num_iters, confidence, prop_missing*100)

    ax = pylab.subplot(3,1,3)
    ax.text(0,0,txt, fontsize=9)
    ax.axis('off')

    if filename is None:
        filename = 'Error_bars_shrink-iters=%i_chains=%i_T=%i.png' % \
            (num_iters, num_chains, int(time.time()))

    pylab.savefig( filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_reasonably_calibrated_errors(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    pylab.locator_params(nbins=3)
    fig = pylab.figure(num=None, figsize=(10,8), facecolor='w', edgecolor='k')

    num_cols = result['config']['num_cols']

    ax = pylab.subplot(2,3,1)
    pylab.plot([0,1],[0,1], color='black', lw=3)
    for col in range(num_cols):
        X = numpy.cumsum(result['actual_frequencies'][col])
        Y = numpy.cumsum(result['inferred_P_cc'][col])
        pylab.plot(X, Y, color='green', alpha = .5, lw=2)

    pylab.ylabel('Inferred frequencies')
    pylab.xlabel('Actual frequencies')
    ax.set_yticks([0,.5,1])
    ax.set_xticks([0,.5,1])
    pylab.title('CrossCat')
    pylab.xlim([0,1])
    pylab.ylim([0,1])


    ax = pylab.subplot(2,3,2)
    pylab.plot([0,1],[0,1], color='black', lw=3)
    for col in range(num_cols):
        X = numpy.cumsum(result['actual_frequencies'][col])
        Y = numpy.cumsum(result['inferred_P_crp'][col])
        pylab.plot(X, Y, color='blue', alpha = .5, lw=2)

    pylab.ylabel('Inferred frequencies')
    pylab.xlabel('Actual frequencies')
    ax.set_yticks([0,.5,1])
    ax.set_xticks([0,.5,1])
    pylab.title('CRP mixture')
    pylab.xlim([0,1])
    pylab.ylim([0,1])

    ax = pylab.subplot(2,3,3)
    pylab.plot([0,1],[0,1], color='black', lw=3)
    for col in range(num_cols):
        X = numpy.cumsum(result['actual_frequencies'][col])
        Y = numpy.cumsum(result['inferred_P_nb'][col])
        pylab.plot(X, Y, color='red', alpha = .5, lw=2)

    pylab.ylabel('Inferred frequencies')
    pylab.xlabel('Actual frequencies')
    ax.set_yticks([0,.5,1])
    ax.set_xticks([0,.5,1])
    pylab.title('Naive Bayes')
    pylab.xlim([0,1])
    pylab.ylim([0,1])

    ax = pylab.subplot(2,3,4)

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_chains = result['config']['num_chains']
    num_views = result['config']['num_views']
    num_clusters = result['config']['num_clusters']
    prop_missing = result['config']['prop_missing']
    multinomial_categories = result['config']['multinomial_categories']

    txt = '''
        Cumulated frequency plots over missing values for multinomial data. Each line 
        represents the distribution of a column. Y-axis is the inferred distribution
        and the x-axis is the actual distribution. Each line can be thought of as a 
        multinomial P-P plot using normalized frequencies over missing values.

        BayesDB: normal configuration
        BayesDB CRP mixture configuration: one view, no column transitions
        BayesDB Naive Bayes configuration: one view, one category, only hyperparameter
        transitions

        The table was %i rows by %i cols with %i views and %i categories per view. Each
        column's data was generates from a multinomial distribution with %i values. %1.2f
        percent of the data was removed.

        %i chains of where run for %i iterations for each configuration.
    ''' % (num_rows, num_cols, num_views, num_clusters, multinomial_categories, prop_missing*100, \
        num_chains, num_iters)

    ax.text(0,0,txt, fontsize=9)
    ax.axis('off')

    if filename is None:
        filename = 'Reasonably_calibrated=%i_chains=%i_T=%i.png' % \
            (num_iters, num_chains, int(time.time()))

    pylab.savefig( filename )
# `````````````````````````````````````````````````````````````````````````````
def plot_estimate_the_full_joint(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    
    fig = pylab.figure(num=None, figsize=(8,10), facecolor='w', edgecolor='k')

    mhp_nb = result['MEAN_P_naive_bayes_indexer']
    mhp_crp = result['MEAN_P_crp_mixture_indexer']
    mhp_cc = result['MEAN_P_crosscat_indexer']

    # plot results
    ax = pylab.subplot(3,1,1)
    pylab.plot( mhp_nb, c='red', lw=3, label='naive Bayes', alpha=.7 )
    pylab.plot( mhp_crp, c='blue', lw=3, label='CRP mixture', alpha=.7)
    pylab.plot( mhp_cc, c='green', lw=3, label='CrossCat', alpha=.7)
    pylab.title('mean held-out probability')
    pylab.ylabel('mean held-out probability')
    pylab.xlabel('iteration')

    pylab.legend()
    ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.xaxis.set_major_locator(MaxNLocator(5))

    mse_nb = result['MSE_naive_bayes_indexer']
    mse_crp = result['MSE_crp_mixture_indexer']
    mse_cc = result['MSE_crosscat_indexer']

    ax = pylab.subplot(3,1,2)
    pylab.plot( mse_nb, c='red', lw=3, label='naive Bayes', alpha=.7 )
    pylab.plot( mse_crp, c='blue', lw=3, label='CRP mixture', alpha=.7)
    pylab.plot( mse_cc, c='green', lw=3, label='CrossCat', alpha=.7)
    pylab.title('MSE')
    pylab.ylabel('MSE')
    pylab.xlabel('iteration')

    pylab.legend()
    ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.xaxis.set_major_locator(MaxNLocator(5))

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_cols = result['config']['num_cols']
    num_chains = result['config']['num_chains']
    num_views = result['config']['num_views']
    num_clusters = result['config']['num_clusters']

    txt = '''
        Top: Mean p over each value of a held-out row from a %i rows by %i columns table.
        The table was randomly generated with %i views and %i categories per view.

        Bottom: Mean squared error of predictive probability over each value in the held-out
        row.

        Green line: BayesDB normal configuration
        Blue line: BayesDB CRP mixture configuration (one view, no column transitions)
        Red line: BayesDB Naive Bayes configuration (one view, one category, only hyperparameter
        transitions)

        PROBABILITY was calculated from %i chains run for %i iterations.
    ''' % (num_rows, num_cols, num_views, num_clusters, num_chains, num_iters)

    if filename is None:
        filename = 'Estimate_full_joint-iters=%i_chains=%i_T=%i.png' % \
            (num_iters, num_chains, int(time.time()))

    ax = pylab.subplot(3,1,3)
    ax.text(-.1,.0,txt, fontsize=10)
    ax.axis('off')

    pylab.savefig( filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_fills_in_the_blanks(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    pylab.locator_params(nbins=3)
    fig = pylab.figure(num=None, figsize=(10,8), facecolor='w', edgecolor='k')

    prop_missing = result['config']['prop_missing']

    ax = pylab.subplot(2,1,1)
    pylab.plot(prop_missing, result['MSE_naive_bayes_indexer'], lw=3, c='red', label='Naive Bayes')
    pylab.plot(prop_missing, result['MSE_crp_mixture_indexer'], lw=3, c='blue', label='CRP mixture')
    pylab.plot(prop_missing, result['MSE_crosscat_indexer'], lw=3, c='green', label='CrossCat')

    ax.set_xticks(prop_missing)
    ax.yaxis.set_major_locator(MaxNLocator(3))
    pylab.ylabel('MSE')
    pylab.xlabel('proportion of data missing')
    pylab.legend(loc=4)

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_cols = result['config']['num_cols']
    num_chains = result['config']['num_chains']
    impute_samples = result['config']['impute_samples']

    txt = '''
        Mean squared error over all imputed missing values (y-axis) for a %i rows by %i table with
        variable proportion of missing data (x-axis).

        Green line: BayesDB normal configuration
        Blue line: BayesDB CRP mixture configuration (one view, no column transitions)
        Red line: BayesDB Naive Bayes configuration (one view, one category, only hyperparameter
        transitions)

        Each imputation was calculated with %i samples from %i chains run for %i iterations.
    ''' % (num_rows, num_cols, impute_samples, num_chains, num_iters)

    if filename is None:
        filename = 'Fills_in_blanks-iters=%i_chains=%i_T=%i.png' % \
            (num_iters, num_chains, int(time.time()))

    ax = pylab.subplot(2,1,2)
    ax.text(0,.5,txt, fontsize=10)
    ax.axis('off')

    pylab.savefig( filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_coin_flip(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    fig = pylab.figure(num=None, figsize=(10,8), facecolor='w', edgecolor='k')

    dependence_probs = result['dependence_probs']

    ax = pylab.subplot(2,1,1)
    q_tar = numpy.nonzero(result['target_marker'])[0]
    q_dis = numpy.nonzero([not r for r in result['target_marker']])[0]
    iteration = result['iteration_index']

    pylab.plot(iteration, dependence_probs[:,q_tar], c='red', alpha=.9, lw=1, zorder=100)
    pylab.plot(iteration, dependence_probs[:,q_dis], c='blue', alpha=.15, lw=1, zorder=1)

    pylab.ylabel("dependence probability")
    pylab.xlabel("iteration")
    pylab.ylim([0,1])
    ax.set_yticks([0,.5,1])
    ax.set_xscale('log')

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_chains = result['config']['num_chains']
    num_ones_cols = result['config']['num_ones_cols']

    txt = '''
        DEPENDENCE PROBABILITY of pairs of columns in a %i rows by %i columns table of
        random binary data. Red lines represent the two pairs of %i added all-ones columns; 
        blue lines are pairs of independent columns.

        DEPENDENCE PROBABILITY was calculated with %i chains over %i iterations.

    ''' % (num_rows, 2**num_rows, num_ones_cols, num_chains, num_iters)

    ax = pylab.subplot(2,1,2)
    ax.text(0,.5,txt, fontsize=10)
    ax.axis('off')

    if filename is None:
        filename = "coin-flip=%s_num_rows=%i-num_chains=%i-num_iters=%i-T=%i.png" % \
        ( str(needles), num_rows, num_chains, num_iters, int(time.time()))

    pylab.savefig( filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_haystacks(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    # pylab.locator_params(nbins=3)
    fig = pylab.figure(num=None, figsize=(10,8), facecolor='w', edgecolor='k')

    independent = result['cols_independent']
    dependence_probs = result['dependence_probs']
    ax = pylab.subplot(2,1,1)
    for q in range(len(independent)):
        is_needle = not independent[q]

        if is_needle:
            pylab.plot(dependence_probs[:,q], c='red', alpha=.9, lw=1, zorder=100)
        else:
            pylab.plot(dependence_probs[:,q], c='blue', alpha=.15, lw=1, zorder=1)

    pylab.ylabel("dependence probability")
    pylab.xlabel("iteration")
    pylab.ylim([0,1])
    # ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.set_yticks([0,.5,1])
    # ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.set_xscale('log')

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_cols = result['config']['num_cols']
    num_chains = result['config']['num_chains']
    data_mode = result['config']['data_mode']
    needles = result['config']['needles']
    independent_clusters = result['config']['independent_clusters']

    if independent_clusters:
        deptxt = "Distractor columns have independent clusterings."
    else:
        deptxt = "Distractor columns have one cluster each."

    if needles:
        txt = '''
            DEPENDENCE PROBABILITY of all pairs of columns in a %i rows by %i columns table of
            %s data. Red lines represent the two pairs of dependent columns; blue lines are 
            pairs of independent columns.

            DEPENDENCE PROBABILITY was calculated with %i chains over %i iterations.

            %s
        ''' % (num_rows, num_cols, data_mode, num_chains, num_iters, deptxt)
    else:
        txt = '''
            DEPENDENCE PROBABILITY of all pairs of columns in a %i rows by %i columns table of
            %s noise. Each line represents the DEPENDENCE PROBABILITY of a pair of columns.

            DEPENDENCE PROBABILITY was calculated with %i chains over %i iterations.

            %s
        ''' % (num_rows, num_cols, data_mode, num_chains, num_iters, deptxt)



    ax = pylab.subplot(2,1,2)
    ax.text(0,.5,txt, fontsize=10)
    ax.axis('off')

    if filename is None:
        filename = "Haystack-Needles=%s_num_rows=%i-num_chains=%i-num_iters=%i-T=%i.png" % \
        ( str(needles), num_rows, num_chains, num_iters, int(time.time()))


    pylab.savefig( filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_haystacks_break(result, filename=None):
    pylab.rcParams.update({'font.size': 8})
    # pylab.locator_params(nbins=3)

    # get figure size by number of column subsamples
    num_plots = len(result['steps'])+2
    plot_height = (num_plots+1)*3
    plot_width = 10

    fig = pylab.figure(num=None, figsize=(plot_width,plot_height), facecolor='w',
            edgecolor='k', tight_layout=True)

    step_idx = 0
    for step_result in result['steps']:
        step_idx += 1
        independent = step_result['cols_independent']
        dependence_probs = step_result['dependence_probs']
        ax = pylab.subplot(num_plots,1,step_idx)
        for q in range(len(independent)):
            is_needle = not independent[q]
            if is_needle:
                pylab.plot(dependence_probs[:,q], c='red', alpha=.9, lw=2, zorder=100)
            else:
                pylab.plot(dependence_probs[:,q], c='blue', alpha=.15, lw=2, zorder=1)

        pylab.ylabel("dependence probability")
        pylab.xlabel("iteration")
        pylab.title("%i distractor columns" % step_result['distractor_cols'])
        pylab.ylim([0,1])
        ax.set_yticks([0,.5,1])
        # ax.xaxis.set_major_locator(MaxNLocator(5))
        # ax.set_xscale('log')


    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    max_cols = result['config']['max_cols']
    rho = result['config']['rho']
    num_chains = result['config']['num_chains']
    multimodal = result['config']['multimodal']
    separation = result['config']['separation']
    independent_clusters = result['config']['independent_clusters']


    X = result['data']
    for col in range(X.shape[1]):
        Z = copy.deepcopy(X[:,col])
        X[:,col] = X[:,col]/numpy.max(numpy.abs(Z))

    ax = pylab.subplot(num_plots,1,num_plots-1)
    im = ax.matshow(X, cmap='YlGnBu')
    pylab.plot([1.5,1.5], [-.5, result['config']['num_rows']-.5], lw=1,c='red')
    pylab.plot([3.5,3.5], [-.5, result['config']['num_rows']-.5], lw=1,c='red')
    pylab.title('scaled data')
    pylab.xlim([-.5,max_cols+4-1.5])
    pylab.ylim([-.5,num_rows-1.5])
    ax.set_aspect('auto')
    # ax.set_yticks('')
    # ax.set_xticks('')
    pylab.colorbar(im, pad=0)

    
    if independent_clusters:
        deptxt = "Distractor columns have independent clusterings."
    else:
        deptxt = "Distractor columns have one cluster each."

    if multimodal:
        datatxt = "Separation of dependent column modes =  %1.2f." % (separation)
    else:
        datatxt = "rho of dependent columns = %1.2f." % (rho)

    txt = '''
        X-axes are log-scaled

        DEPENDENCE PROBABILITY of all pairs of columns in a %i rows by %i columns table of
        continuous data. Red lines represent the two pairs of dependent columns; blue lines are 
        pairs of independent columns.

        DEPENDENCE PROBABILITY was calculated with %i chains over %i iterations.

        %s.

        %s
    ''' % (num_rows, max_cols, num_chains, num_iters, datatxt, deptxt)

    ax = pylab.subplot(num_plots,1,num_plots)
    ax.text(0,.5,txt, fontsize=10)
    ax.axis('off')

    if filename is None:
        base_filename = "Haystack-Break-num_rows=%i-num_chains=%i-num_iters=%i-T=%i" % \
        ( num_rows, num_chains, num_iters, int(time.time()))
        img_filename = base_filename + '.png'
    else:
        img_filename = filename


    pylab.savefig( img_filename )

# `````````````````````````````````````````````````````````````````````````````
def plot_recovers_original_densities(result, filename=None):

    pylab.rcParams.update({'font.size': 8})
    pylab.locator_params(nbins=3)
    fig = pylab.figure(num=None, figsize=(10,8), facecolor='w', edgecolor='k')

    plt = 0
    for shape in ["sinwave", "x", "ring", "dots"]:
        key = shape + "_original"
        X_original = result[key]
        ax = pylab.plt.subplot2grid((3,4), (0, plt))
        pylab.scatter( X_original[:,0], X_original[:,1], color='blue', edgecolor='none', alpha=.2 )
        pylab.title("%s original" % shape)
        ax.yaxis.set_major_locator(MaxNLocator(3))
        ax.xaxis.set_major_locator(MaxNLocator(3))

        key = shape + "_inferred"
        X_inferred = result[key]
        ax1 = pylab.plt.subplot2grid((3,4), (1, plt))
        pylab.scatter( X_inferred[:,0], X_inferred[:,1], color='red', edgecolor='none', alpha=.2 )
        pylab.xlim(ax.get_xlim())
        pylab.ylim(ax.get_ylim())
        pylab.title("%s inferred" % shape)
        ax1.yaxis.set_major_locator(MaxNLocator(3))
        ax1.xaxis.set_major_locator(MaxNLocator(3))

        plt += 1

    num_iters = result['config']['num_iters']
    num_rows = result['config']['num_rows']
    num_chains = result['config']['num_chains']

    txt = '''
        Top panels: zero-correlation datasets consisting of %i points. 
        Bottom panels: result of SIMULATE %i datapoints after running %i 
        chains for %i iterations with %s datatype.
    ''' % (num_rows, num_rows, num_chains, num_iters, result['config']['datatype'])

    pylab.plt.subplot2grid((3,3), (2,0), colspan=3)

    ax = pylab.gca()
    ax.text(0,.5,txt, fontsize=10)
    ax.axis('off')

    if filename is None:
        filename = "Recovers_original_densities-num_rows=%i-num_chains=%i-num_iters=%i-T=%i.png" % \
        (num_rows, num_chains, num_iters, int(time.time()))

    pylab.savefig(filename)
