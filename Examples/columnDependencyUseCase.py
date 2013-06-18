# Using CrossCat to Examine Column Dependencies
# 1. Import packages/modules needed
import numpy 
import pylab
pylab.ion()
pylab.show()
#
import tabular_predDB.python_utils.data_utils as du
import tabular_predDB.python_utils.plot_utils as pu
import tabular_predDB.CrossCatClient as ccc


# 2. Load a data table from csv file. In this example, we use synthetic data
filename = 'flight_data_subset.csv'
filebase = 'flight_data_subset'
T, M_r, M_c = du.read_model_data_from_csv(filename, gen_seed=0)
T_array = numpy.asarray(T)
num_rows = len(T)
num_cols = len(T[0])
col_names = numpy.array([M_c['idx_to_name'][str(col_idx)] for col_idx in range(num_cols)])
dataplot_filename = '{!s}_data'.format(filebase)

pu.plot_T(T_array, M_c, filename = dataplot_filename)

for colindx in range(len(col_names)):
    print 'Attribute: {0:30}   Model:{1}'.format(col_names[colindx],M_c['column_metadata'][colindx]['modeltype'])

# 3. Initialize CrossCat Engine and Build Model
engine = ccc.get_CrossCatClient('local', seed = 0)
X_L_list = []
X_D_list = []
numChains = 10
num_transitions = 10

for chain_idx in range(numChains):
    print 'Chain {!s}'.format(chain_idx)
    M_c_prime, M_r_prime, X_L, X_D = engine.initialize(M_c, M_r, T)
    X_L_prime, X_D_prime = engine.analyze(M_c, T, X_L, X_D, kernel_list=(),
                                          n_steps=num_transitions)
    X_L_list.append(X_L_prime)
    X_D_list.append(X_D_prime)

# 4. Visualize clusters in one sample drawn from the model 
viewplot_filename = '{!s}_view'.format(filebase)
pu.plot_views(T_array, X_D_list[4], X_L_list[4], M_c, filename= viewplot_filename)

zplot_filename = '{!s}_feature_z'.format(filebase)
# 5. Construct and plot column dependency matrix
pu.do_gen_feature_z(X_L_list, X_D_list, M_c, zplot_filename, filename)
