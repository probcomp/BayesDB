from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.map cimport map as c_map
from libcpp.set cimport set as c_set
from cython.operator import dereference
cimport numpy as np
#
import numpy
#
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.plot_utils as pu


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
          double transition_features(matrix[double] data)
          double transition_views(matrix[double] data)
          double transition_view_i(int i, matrix[double] data)
          double transition_column_crp_alpha()
          # getters
          double get_column_crp_alpha()
          double get_column_crp_score()
          double get_data_score()
          double get_marginal_logp()
          int get_num_views()
          c_map[int, c_set[int]] get_column_groups()
          string to_string(string join_str, bool top_level)
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

cdef class p_State:
    cdef State *thisptr
    cdef matrix[double] *dataptr
    cdef vector[int] gri
    cdef vector[int] gci
    cdef vector[string] column_types
    cdef vector[int] event_counts
    cdef np.ndarray T_array

    def __cinit__(self, M_c, T, X_L=None, X_D=None, initialization=None,
                  N_GRID=11, SEED=0):
         # FIXME: actually use initialization 
         # modify State.pyx to accept column_types, event_counts
         # modify State.{h,cpp} to accept column_types, event_counts
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
         #
         must_initialize = X_L is None
         if must_initialize:
              self.thisptr = new_State(dereference(self.dataptr),
                                       self.column_types,
                                       self.event_counts,
                                       self.gri, self.gci,
                                       N_GRID, SEED)
         else:
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
    def plot(self, save_str_prefix='', iter_idx=None):
         T_array = self.T_array
         X_D = self.get_X_D()
         X_L = self.get_X_L()
         #
         if iter_idx is not None:
              save_str_prefix = 'iter_%s_' % iter_idx
         pu.plot_views(T_array, X_D, X_L, save_str_prefix)
    def plot_T(self, save_str='T'):
         T_array = self.T_array
         pu.plot_T(T_array, save_str)
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
         column_groups = self.thisptr.get_column_groups()
         return column_groups[view_idx]
    def get_column_component_suffstats_i(self, view_idx):
          return self.thisptr.get_column_component_suffstats_i(view_idx)
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
    def transition(self):
        return self.thisptr.transition(dereference(self.dataptr))
    def transition_features(self):
        return self.thisptr.transition_features(dereference(self.dataptr))
    def transition_views(self):
        return self.thisptr.transition_views(dereference(self.dataptr))
    def transition_view_i(self, i):
        return self.thisptr.transition_view_i(i, dereference(self.dataptr))
    def transition_column_crp_alpha(self):
        return self.thisptr.transition_column_crp_alpha()
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
         return X_L
    def save(self, filename, **kwargs):
         save_dict = dict(
              X_L=self.get_X_L(),
              X_D=self.get_X_D(),
              )
         save_dict.update(**kwargs)
         fu.pickle(save_dict, filename)

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

def transform_latent_state_to_constructor_args(X_L, X_D):
     extract_row_partition_alpha = lambda view_state: \
         view_state['row_partition_model']['hypers']['log_alpha']
     num_rows = len(X_D[0])
     num_cols = len(X_L['column_hypers'])
     #
     global_row_indices = range(num_rows)
     global_col_indices = range(num_cols)
     hypers_m = dict(zip(global_col_indices, X_L['column_hypers']))
     hypers_m = floatify_dict_dict(hypers_m)
     column_indicator_list = X_L['column_partition']['assignments']
     column_partition = indicator_list_to_list_of_list(column_indicator_list)
     column_crp_alpha = \
         numpy.exp(X_L['column_partition']['hypers']['log_alpha'])
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
