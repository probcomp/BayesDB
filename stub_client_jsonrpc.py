import time
import requests
import json
#
import numpy
#
import Engine as E


# settings
URI = 'http://localhost:8007'
id = 0

import sys
def gen_data(gen_seed, num_clusters, num_cols, num_rows, max_mean=10, max_std=1):
    n_grid = 11
    mu_grid = numpy.linspace(-max_mean, max_mean, n_grid)
    sigma_grid = 10 ** numpy.linspace(-1, numpy.log10(max_std), n_grid)
    num_rows_per_cluster = num_rows / num_clusters
    zs = numpy.repeat(range(num_clusters), num_rows_per_cluster)
    #
    random_state = numpy.random.RandomState(gen_seed)
    #
    which_mus = random_state.randint(len(mu_grid), size=(num_clusters,num_cols))
    which_sigmas = random_state.randint(len(sigma_grid), size=(num_clusters,num_cols))
    mus = mu_grid[which_mus]
    sigmas = sigma_grid[which_sigmas]
    clusters = []
    for row_mus, row_sigmas in zip(mus, sigmas):
        cluster_columns = []
        for mu, sigma in zip(row_mus, row_sigmas):
            cluster_column = random_state.normal(mu, sigma, num_rows_per_cluster)
            cluster_columns.append(cluster_column)
        cluster = numpy.vstack(cluster_columns).T
        clusters.append(cluster)
    xs = numpy.vstack(clusters)
    return xs, zs

def gen_factorial_data(gen_seed, num_clusters, num_cols, num_rows, num_splits,
                       max_mean=10, max_std=1):
    random_state = numpy.random.RandomState(gen_seed)
    data_list = []
    inverse_permutation_indices_list = []
    for data_idx in xrange(num_splits):
        data_i, zs_i = gen_data(
            gen_seed=random_state.randint(sys.maxint),
            num_clusters=num_clusters,
            num_cols=num_cols/num_splits,
            num_rows=num_rows,
            )
        permutation_indices = numpy.random.permutation(xrange(num_rows))
        inverse_permutation_indices = numpy.argsort(permutation_indices)
        inverse_permutation_indices_list.append(inverse_permutation_indices)
        data_list.append(numpy.array(data_i)[permutation_indices])
    data = numpy.hstack(data_list)
    return data, inverse_permutation_indices_list

# helper functions
def create_message(method_name, params):
    global id
    id += 1
    message = {
        'jsonrpc': '2.0',
        'method': method_name,
        'params': params,
        'id': str(id),
        }
    return json.dumps(message)

def call_and_print(method_name, args_dict):
    message = create_message(method_name, args_dict)
    print 'trying message:', message
    r = requests.put(URI, data=message)
    r.raise_for_status()
    out = json.loads(r.content)
    print out
    print
    if isinstance(out, dict) and 'result' in out:
        return out['result']
    else:
        # error?
        return out

# random_state = numpy.random.RandomState(0)
# T_dim = (10, 10)
# T = (numpy.arange(numpy.prod(T_dim)).reshape(T_dim) * 1.0).tolist()
T, data_inverse_permutation_indices = \
    gen_factorial_data(0, 2, 6, 20, 2, max_mean=10, max_std=0.1)
T = T.tolist()

# non-stub functions
non_stub = set(['initialize', 'initialize_and_analyze', 'analyze', 'impute',
                'simple_predictive_sample'])

method_name = 'initialize'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['M_r'] = 'M_r'
args_dict['i'] = ''
args_dict['T'] = T
out = call_and_print(method_name, args_dict)
#
method_name = 'initialize_and_analyze'
args_dict = dict()
args_dict['n_steps'] = 10
args_dict['SEED'] = 0
args_dict['T'] = T
out = call_and_print(method_name, args_dict)
#
X_L_prime, X_D_prime = out
method_name = 'analyze'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['T'] = T
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['kernel_list'] = 'kernel_list'
args_dict['n_steps'] = 10
args_dict['c'] = 'c'
args_dict['r'] = 'r'
args_dict['max_iterations'] = 'max_iterations'
args_dict['max_time'] = 'max_time'
out = call_and_print(method_name, args_dict)
X_L_prime, X_D_prime = out
time.sleep(1)

method_name = 'impute'
args_dict = dict()
args_dict['M_c'] = 'M_c'
args_dict['X_L'] = 'X_L'
args_dict['X_D'] = 'X_D'
args_dict['Y'] = 'Y'
args_dict['q'] = range(3)
args_dict['n'] = 'n'
out = call_and_print(method_name, args_dict)
time.sleep(1)

num_cols = len(T[0])
idx_to_name = dict(zip(range(num_cols),range(num_cols)))
column_metadata=[None for idx in range(num_cols)]
M_c = dict(idx_to_name=idx_to_name, column_metadata=column_metadata)
#
method_name = 'simple_predictive_sample'
args_dict = dict()
args_dict['M_c'] = M_c
for view_state_i in X_L_prime['view_state']:
    view_state_i['column_names'] = range(5)
args_dict['X_L'] = X_L_prime
args_dict['X_D'] = X_D_prime
args_dict['Y'] = None
args_dict['q'] = (0,0)
values = []
for idx in range(10):
    out = call_and_print(method_name, args_dict)
    values.append(out[0])
print values
time.sleep(1)


# programmatically call all the other method calls
method_name_to_args = E.get_method_name_to_args()
for method_name, arg_str_list in method_name_to_args.iteritems():
    if method_name in non_stub:
        print 'skipping non-stub method:', method_name
        print
        continue
    args_dict = dict(zip(arg_str_list, arg_str_list))
    call_and_print(method_name, args_dict)
    time.sleep(1)
