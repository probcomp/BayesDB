#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.map cimport map as c_map
from cython.operator import dereference
cimport numpy as np
#
import numpy
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.general_utils as gu
# import tabular_predDB.python_utils.plot_utils as pu


cdef double set_double(double& to_set, double value):
     to_set = value
     return to_set

cdef vector[int] convert_int_vector_to_cpp(python_vector):
     cdef vector[int] ret_vec
     for value in python_vector:
          ret_vec.push_back(value)
     return ret_vec

cdef vector[string] convert_string_vector_to_cpp(python_vector):
     cdef vector[string] ret_vec
     cdef string str
     for value in python_vector:
          str = value
          ret_vec.push_back(str)
     return ret_vec

cdef extern from "<boost/numeric/ublas/matrix.hpp>" namespace "boost::numeric::ublas":
    cdef cppclass matrix[double]:
        void clear()
        int size1()
        int size2()
        double& operator()(int i, int j)
    matrix[double] *new_matrix "new boost::numeric::ublas::matrix<double>" (int i, int j)
    void del_matrix "delete" (matrix *m)

cdef class p_matrix:
    cdef matrix[double] *thisptr
    def __cinit__(self, i, j):
          self.thisptr = new_matrix(i, j)
    def __dealloc__(self):
        del_matrix(self.thisptr)
    def size1(self):
        return self.thisptr.size1()
    def size2(self):
        return self.thisptr.size2()
    def get(self, i, j):
         # cdef matrix[double] m = dereference(self.thisptr)
         # this doesn't work: error: ‘operator()’ not defined
         # return m(i,j) 
         #
         # this doesn't work: Object of type 'matrix[double]' has
         #   no attribute 'operator'
         # return m.operator()(i,j) 
        return dereference(self.thisptr)(i,j)
    def set(self, i, j, val):
         # this doesn't work: Cannot assign to or delete this
         # dereference(self.thisptr)(i,j) = val
         #
         # this doesn't work: error: ‘__pyx_v_intermediate’ declared as
         #   reference but not initialized
         # cdef double &intermediate = dereference(self.thisptr)(i,j)
         set_double(dereference(self.thisptr)(i,j), val)
         return dereference(self.thisptr)(i,j)
    def __repr__(self):
         print_tuple = (self.thisptr.size1(), self.thisptr.size2())
         return "matrix[%s, %s]" % print_tuple

cdef matrix[double]* convert_data_to_cpp(np.ndarray[np.float64_t, ndim=2] data):
     cdef int num_rows = data.shape[0]
     cdef int num_cols = data.shape[1]
     dataptr = new_matrix(num_rows, num_cols)
     cdef int i,j
     for i from 0 <= i < num_rows:
          for j from 0 <= j < num_cols:
               set_double(dereference(dataptr)(i,j), data[i,j])
     return dataptr

cdef extern from "State.h":
     cdef cppclass State:
          # mutators
          double transition(matrix[double] data)
          double transition_column_crp_alpha()
          double transition_features(matrix[double] data, vector[int] which_cols)
          double transition_column_hyperparameters(vector[int] which_cols)
          double transition_row_partition_hyperparameters(vector[int] which_cols)
          double transition_row_partition_assignments(matrix[double] data, vector[int] which_rows)
          double transition_views(matrix[double] data)
          double transition_view_i(int i, matrix[double] data)
          double transition_views_row_partition_hyper()
          double transition_views_col_hypers()
          double transition_views_zs(matrix[double] data)
          double calc_row_predictive_logp(vector[double] in_vd)
          # getters
          double get_column_crp_alpha()
          double get_column_crp_score()
          double get_data_score()
          double get_marginal_logp()
          int get_num_views()
          c_map[int, vector[int]] get_column_groups()
          string to_string(string join_str, bool top_level)
          double draw_rand_u()
          int draw_rand_i()
          # API helpers
          vector[c_map[string, double]] get_column_hypers()
          c_map[string, double] get_column_partition_hypers()
          vector[int] get_column_partition_assignments()
          vector[int] get_column_partition_counts()
          #
          c_map[string, double] get_row_partition_model_hypers_i(int view_idx)
          vector[int] get_row_partition_model_counts_i(int view_idx)
          vector[vector[c_map[string, double]]] get_column_component_suffstats_i(int view_idx)
          #
          vector[vector[int]] get_X_D()
          void SaveResult()
     State *new_State "new State" (matrix[double] &data,
                                   vector[string] global_col_datatypes,
                                   vector[int] global_col_multinomial_counts,
                                   vector[int] global_row_indices,
                                   vector[int] global_col_indices,
                                   string col_initialization,
                                   string row_initialization,
                                   int N_GRID, int SEED)
     State *new_State "new State" (matrix[double] &data,
                                   vector[string] global_col_datatypes,
                                   vector[int] global_col_multinomial_counts,
                                   vector[int] global_row_indices,
                                   vector[int] global_col_indices,
                                   c_map[int, c_map[string, double]] hypers_m,
                                   vector[vector[int]] column_partition,
                                   double column_crp_alpha,
                                   vector[vector[vector[int]]] row_partition_v,
                                   vector[double] row_crp_alpha_v,
                                   int N_GRID, int SEED)
     void del_State "delete" (State *s)


def extract_column_types_counts(M_c):
    column_types = [
        column_metadata['modeltype']
        for column_metadata in M_c['column_metadata']
        ]
    event_counts = [
        len(column_metadata.get('value_to_code',[]))
        for column_metadata in M_c['column_metadata']
        ]
    return column_types, event_counts

def get_args_dict(args_list, vars_dict):
     args_dict = dict([
               (arg, vars_dict[arg])
               for arg in args_list
               ])
     return args_dict

transition_name_to_method_name_and_args = dict(
     column_partition_hyperparameter=('transition_column_crp_alpha', []),
     column_partition_assignments=('transition_features', ['c']),
     column_hyperparameters=('transition_column_hyperparameters', ['c']),
     row_partition_hyperparameters= ('transition_row_partition_hyperparameters', ['c']),
     row_partition_assignments=('transition_row_partition_assignments', ['r']),
     )

def get_all_transitions_permuted(seed):
     which_transitions = transition_name_to_method_name_and_args.keys()
     random_state = numpy.random.RandomState(seed)
     which_transitions = random_state.permutation(which_transitions)
     return which_transitions

cdef class p_State:
    cdef State *thisptr
    cdef matrix[double] *dataptr
    cdef vector[int] gri
    cdef vector[int] gci
    cdef vector[string] column_types
    cdef vector[int] event_counts
    cdef np.ndarray T_array
    cpdef M_c

    def __cinit__(self, M_c, T, X_L=None, X_D=None,
                  initialization='from_the_prior', row_initialization=-1,
                  N_GRID=31, SEED=0):
         column_types, event_counts = extract_column_types_counts(M_c)
         global_row_indices = range(len(T))
         global_col_indices = range(len(T[0]))
         #
         # FIXME: keeping TWO copies of the data here
         self.T_array = numpy.array(T)
         self.dataptr = convert_data_to_cpp(self.T_array)
         self.column_types = convert_string_vector_to_cpp(column_types)
         self.event_counts = convert_int_vector_to_cpp(event_counts)
         self.gri = convert_int_vector_to_cpp(global_row_indices)
         self.gci = convert_int_vector_to_cpp(global_col_indices)
         self.M_c = M_c
         #
         must_initialize = X_L is None
         if must_initialize:
              col_initialization = initialization
              if row_initialization == -1:
                   row_initialization = initialization
              self.thisptr = new_State(dereference(self.dataptr),
                                       self.column_types,
                                       self.event_counts,
                                       self.gri, self.gci,
                                       col_initialization,
                                       row_initialization,
                                       N_GRID, SEED)
         else:
              # # !!! MUTATES X_L !!!
              desparsify_X_L(M_c, X_L)
              constructor_args = \
                  transform_latent_state_to_constructor_args(X_L, X_D)
              hypers_m = constructor_args['hypers_m']
              column_partition = constructor_args['column_partition']
              column_crp_alpha = constructor_args['column_crp_alpha']
              row_partition_v = constructor_args['row_partition_v']
              row_crp_alpha_v = constructor_args['row_crp_alpha_v']
              self.thisptr = new_State(dereference(self.dataptr),
                                       self.column_types,
                                       self.event_counts,
                                       self.gri, self.gci,
                                       hypers_m,
                                       column_partition, column_crp_alpha,
                                       row_partition_v, row_crp_alpha_v,
                                       N_GRID, SEED)
    def __dealloc__(self):
        del_matrix(self.dataptr)
        del_State(self.thisptr)
    def __repr__(self):
         print_tuple = (
              self.dataptr.size1(),
              self.dataptr.size2(),
              self.thisptr.to_string(";", False),
              )
         return "State[%s, %s]:\n%s" % print_tuple
    def to_string(self, join_str='\n', top_level=False):
         return self.thisptr.to_string(join_str, top_level)
    # def plot(self, M_c, filename=None, dir=''):
    #      T_array = self.T_array
    #      X_D = self.get_X_D()
    #      X_L = self.get_X_L()
    #      pu.plot_views(T_array, X_D, X_L, M_c, filename, dir)
    # def plot_T(self, M_c, filename=None, dir=''):
    #      T_array = self.T_array
    #      pu.plot_T(T_array, M_c, filename, dir)
    #
    # getters
    def get_column_groups(self):
        return self.thisptr.get_column_groups()
    def get_column_crp_alpha(self):
         return self.thisptr.get_column_crp_alpha()
    def get_column_crp_score(self):
         return self.thisptr.get_column_crp_score()
    def get_data_score(self):
         return self.thisptr.get_data_score()
    def get_marginal_logp(self):
        return self.thisptr.get_marginal_logp()
    def get_num_views(self):
        return self.thisptr.get_num_views()
    def calc_row_predictive_logp(self, in_vd):
         return self.thisptr.calc_row_predictive_logp(in_vd)
    #
    # get_X_L helpers helpers
    def get_row_partition_model_i(self, view_idx):
          hypers = self.thisptr.get_row_partition_model_hypers_i(view_idx)
          counts = self.thisptr.get_row_partition_model_counts_i(view_idx)
          row_partition_model_i = dict()
          row_partition_model_i['hypers'] = hypers
          row_partition_model_i['counts'] = counts
          return row_partition_model_i
    def get_column_names_i(self, view_idx):
         idx_to_name = self.M_c['idx_to_name']
         column_groups = self.thisptr.get_column_groups()
         #
         column_indices_i = column_groups[view_idx]
         column_indices_i = map(str, column_indices_i)
         column_names_i = []
         for idx in column_indices_i:
              if idx not in idx_to_name:
                   print "%s not in %s" % (idx, idx_to_name)
              value = idx_to_name[idx]
              column_names_i.append(value)
         return column_names_i
    def get_column_component_suffstats_i(self, view_idx):
         column_component_suffstats = \
             self.thisptr.get_column_component_suffstats_i(view_idx)
         # FIXME: make this actually work
         #        should sparsify here rather than later in get_X_L
         # column_names = self.get_column_names_i(view_idx)
         # for col_name, column_component_suffstats_i in \
         #          zip(column_names, column_component_suffstats):
         #     modeltype = get_modeltype_from_name(self.M_c, col_name)
         #     if modeltype == 'symmetric_dirichlet_discrete':
         #         sparsify_column_component_suffstats(column_component_suffstats_i)
         return column_component_suffstats
    def get_view_state_i(self, view_idx):
          row_partition_model = self.get_row_partition_model_i(view_idx)
          column_names = self.get_column_names_i(view_idx)
          column_component_suffstats = \
              self.get_column_component_suffstats_i(view_idx)
          view_state_i = dict()
          view_state_i['row_partition_model'] = row_partition_model
          view_state_i['column_names'] = list(column_names)
          view_state_i['column_component_suffstats'] = \
              column_component_suffstats
          return view_state_i
    # get_X_L helpers
    def get_column_partition(self):
        hypers = self.thisptr.get_column_partition_hypers()
        assignments = self.thisptr.get_column_partition_assignments()
        counts = self.thisptr.get_column_partition_counts()
        column_partition = dict()
        column_partition['hypers'] = hypers
        column_partition['assignments'] = assignments
        column_partition['counts'] = counts
        return column_partition
    def get_column_hypers(self):
        return self.thisptr.get_column_hypers()
    def get_view_state(self):
        view_state = []
        for view_idx in range(self.get_num_views()):
            view_state_i = self.get_view_state_i(view_idx)
            view_state.append(view_state_i)
        return view_state
    # mutators
    def transition(self, which_transitions=(), n_steps=1,
                   c=(), r=(), max_iterations=-1, max_time=-1):
         score_delta = 0
         if len(which_transitions) == 0:
              seed = self.thisptr.draw_rand_i()
              which_transitions = get_all_transitions_permuted(seed)
         with gu.Timer('transition', verbose=False) as timer:
              for step_idx in range(n_steps):
                   for which_transition in which_transitions:
                        elapsed_secs = timer.get_elapsed_secs()
                        if (max_time != -1) and (max_time < elapsed_secs):
                             break
                        method_name_and_args = transition_name_to_method_name_and_args.get(which_transition)
                        if method_name_and_args is not None:
                             method_name, args_list = method_name_and_args
                             which_method = getattr(self, method_name)
                             args_dict = get_args_dict(args_list, locals())
                             score_delta += which_method(**args_dict)
                        else:
                             print_str = 'INVALID TRANSITION TYPE TO' \
                                 'State.transition: %s' % which_transition
                             print print_str
         return score_delta
    def transition_column_crp_alpha(self):
         return self.thisptr.transition_column_crp_alpha()
    def transition_features(self, c=()):
        return self.thisptr.transition_features(dereference(self.dataptr), c)
    def transition_column_hyperparameters(self, c=()):
         return self.thisptr.transition_column_hyperparameters(c)
    def transition_row_partition_hyperparameters(self, c=()):
         return self.thisptr.transition_row_partition_hyperparameters(c)
    def transition_row_partition_assignments(self, r=()):
         return self.thisptr.transition_row_partition_assignments(dereference(self.dataptr), r)
    def transition_views(self):
        return self.thisptr.transition_views(dereference(self.dataptr))
    def transition_view_i(self, i):
        return self.thisptr.transition_view_i(i, dereference(self.dataptr))
    def transition_views_col_hypers(self):
         return self.thisptr.transition_views_col_hypers()
    def transition_views_row_partition_hyper(self):
         return self.thisptr.transition_views_row_partition_hyper()
    def transition_views_zs(self):
         return self.thisptr.transition_views_zs(dereference(self.dataptr))
    # API getters
    def get_X_D(self):
          return self.thisptr.get_X_D()
    def get_X_L(self):
          column_partition = self.get_column_partition()
          column_hypers = self.get_column_hypers()
          view_state = self.get_view_state()
          X_L = dict()
          X_L['column_partition'] = column_partition
          X_L['column_hypers'] = column_hypers
          X_L['view_state'] = view_state
          sparsify_X_L(self.M_c, X_L)
          return X_L
    def save(self, filename, dir='', **kwargs):
         save_dict = dict(
              X_L=self.get_X_L(),
              X_D=self.get_X_D(),
              )
         save_dict.update(**kwargs)
         fu.pickle(save_dict, filename, dir=dir)

def indicator_list_to_list_of_list(indicator_list):
     list_of_list = []
     num_clusters = max(indicator_list) + 1
     import numpy
     for cluster_idx in range(num_clusters):
          which_rows = numpy.array(indicator_list)==cluster_idx
          list_of_list.append(numpy.nonzero(which_rows)[0])
     return list_of_list

def floatify_dict(in_dict):
     for key in in_dict:
          in_dict[key] = float(in_dict[key])
     return in_dict

def floatify_dict_dict(in_dict):
     for key in in_dict:
          in_dict[key] = floatify_dict(in_dict[key])
     return in_dict

def extract_row_partition_alpha(view_state):
     hypers = view_state['row_partition_model']['hypers']
     alpha = hypers.get('alpha')
     if alpha is None:
          log_alpha = hypers['log_alpha']
          alpha = numpy.exp(log_alpha)
     return alpha

def transform_latent_state_to_constructor_args(X_L, X_D):
     num_rows = len(X_D[0])
     num_cols = len(X_L['column_hypers'])
     #
     global_row_indices = range(num_rows)
     global_col_indices = range(num_cols)
     hypers_m = dict(zip(global_col_indices, X_L['column_hypers']))
     hypers_m = floatify_dict_dict(hypers_m)
     column_indicator_list = X_L['column_partition']['assignments']
     column_partition = indicator_list_to_list_of_list(column_indicator_list)
     column_crp_alpha = X_L['column_partition']['hypers']['alpha']
     row_partition_v = map(indicator_list_to_list_of_list, X_D)
     row_crp_alpha_v = map(extract_row_partition_alpha, X_L['view_state'])
     n_grid = 31
     seed = 0
     #
     constructor_args = dict()
     constructor_args['global_row_indices'] = global_row_indices
     constructor_args['global_col_indices'] = global_col_indices
     constructor_args['hypers_m'] = hypers_m
     constructor_args['column_partition'] = column_partition
     constructor_args['column_crp_alpha'] = column_crp_alpha
     constructor_args['row_partition_v'] = row_partition_v
     constructor_args['row_crp_alpha_v'] = row_crp_alpha_v
     constructor_args['N_GRID'] = n_grid
     constructor_args['SEED'] = seed
     #
     return constructor_args

def remove_zero_values(dict_in):
     for key in dict_in.keys():
          if dict_in[key] == 0:
               dict_in.pop(key)
     return dict_in

def insert_zero_values(dict_in, N_keys):
     for key in range(N_keys):
          key_str = str(key)
          if key_str not in dict_in:
               dict_in[key_str] = 0.0
     return dict_in

def sparsify_column_component_suffstats(column_component_suffstats):
     for idx, suffstats_i in enumerate(column_component_suffstats):
          suffstats_i = remove_zero_values(suffstats_i).copy()
          column_component_suffstats[idx] = suffstats_i
     return None

def desparsify_column_component_suffstats(column_component_suffstats,
                                          N_keys):
     for idx, suffstats_i in enumerate(column_component_suffstats):
          insert_zero_values(suffstats_i, N_keys)
     return None

def get_column_component_suffstats_by_global_col_idx(M_c, X_L, col_idx):
     col_name = M_c['idx_to_name'][str(col_idx)]
     view_idx = X_L['column_partition']['assignments'][col_idx]
     view_state_i = X_L['view_state'][view_idx]
     within_view_idx = view_state_i['column_names'].index(col_name)
     column_component_suffstats_i = view_state_i['column_component_suffstats'][within_view_idx]
     return column_component_suffstats_i
     
def sparsify_X_L(M_c, X_L):
     for col_idx, col_i_metadata in enumerate(M_c['column_metadata']):
          modeltype = col_i_metadata['modeltype']
          if modeltype != 'symmetric_dirichlet_discrete':
               continue
          column_component_suffstats_i = \
              get_column_component_suffstats_by_global_col_idx(M_c, X_L,
                                                               col_idx)
          sparsify_column_component_suffstats(column_component_suffstats_i)
     return None

def desparsify_X_L(M_c, X_L):
     for col_idx, col_i_metadata in enumerate(M_c['column_metadata']):
          modeltype = col_i_metadata['modeltype']
          if modeltype != 'symmetric_dirichlet_discrete':
               continue
          column_component_suffstats_i = \
              get_column_component_suffstats_by_global_col_idx(M_c, X_L,
                                                               col_idx)
          N_keys = len(col_i_metadata['value_to_code'])
          desparsify_column_component_suffstats(column_component_suffstats_i,
                                                N_keys)
     return None

def get_modeltype_from_name(M_c, col_name):
    global_col_idx = M_c['name_to_idx'][col_name]
    modeltype = M_c['column_metadata'][global_col_idx]['modeltype']
    return modeltype
