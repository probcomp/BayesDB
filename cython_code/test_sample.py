import argparse
import sys
from collections import Counter
#
import numpy
import pylab
pylab.ion()
pylab.show()
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.sample_utils as su
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.python_utils.api_utils as au


# parse some arguments
parser = argparse.ArgumentParser()
parser.add_argument('pkl_name', type=str)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--hostname', default='127.0.0.1', type=str)
args = parser.parse_args()
pkl_name = args.pkl_name
inf_seed = args.inf_seed
hostname = args.hostname

# FIXME: getting weird error on conversion to int: too large from inside pyx
def get_next_seed(max_val=32767): # sys.maxint):
    return random_state.randint(max_val)

# resume from saved name
save_dict = fu.unpickle(pkl_name)
random_state = numpy.random.RandomState(inf_seed)
M_c = save_dict['M_c']
X_L = save_dict['X_L']
X_D = save_dict['X_D']

# FIXME: test constraints
# Y = [su.Bunch(index=2,value=2.3), su.Bunch(index=0,value=-4.)]
Y = None

# test simple_predictive_sample_observed LOCALLY
views_replicating_samples_params = su.determine_replicating_samples_params(X_L, X_D)
views_samples = []
for replicating_samples_params in views_replicating_samples_params:
    this_view_samples = []
    for replicating_sample_params in replicating_samples_params:
        this_view_this_sample = su.simple_predictive_sample(
            M_c, X_L, X_D, get_next_seed=get_next_seed, **replicating_sample_params)
        this_view_samples.extend(this_view_this_sample)
    views_samples.append(this_view_samples)
for view_idx, view_samples in enumerate(views_samples):
    data_array = numpy.array(view_samples)
    pu.plot_T(data_array)
    pylab.title('simple_predictive_sample observed, view %s on local' % view_idx)

# test simple_predictive_sample_observed REMOTE
# hostname = 'ec2-23-22-208-4.compute-1.amazonaws.com'
URI = 'http://' + hostname + ':8007'
method_name = 'simple_predictive_sample'
#
views_samples = []
for replicating_samples_params in views_replicating_samples_params:
    this_view_samples = []
    for replicating_sample_params in replicating_samples_params:
        args_dict = dict(
            M_c=save_dict['M_c'],
            X_L=save_dict['X_L'],
            X_D=save_dict['X_D'],
            Y=replicating_sample_params['Y'],
            Q=replicating_sample_params['Q'],
            n=replicating_sample_params['n'],
            )
        this_view_this_sample, id = au.call(
            method_name, args_dict, URI)
        print id
        this_view_samples.extend(this_view_this_sample)
    views_samples.append(this_view_samples)
for view_idx, view_samples in enumerate(views_samples):
    data_array = numpy.array(view_samples)
    pu.plot_T(data_array)
    pylab.title('simple_predictive_sample observed, view %s on remote' % view_idx)

# test simple_predictive_sample_unobserved
observed_Q = views_replicating_samples_params[0][0]['Q']
Q = [(1E6, old_tuple[1]) for old_tuple in observed_Q]
new_row_samples = []
new_row_sample = su.simple_predictive_sample(
    M_c, X_L, X_D, Y, Q, get_next_seed, n=1000)
new_row_samples.extend(new_row_sample)
new_row_samples = numpy.array(new_row_samples)
pu.plot_T(new_row_samples)

# test impute
# imputed_value = su.impute(M_c, X_L, X_D, Y, [Q[3]], 100, get_next_seed)
