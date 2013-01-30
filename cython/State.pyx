from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.map cimport map as c_map
from libcpp.set cimport set
from cython.operator import dereference
cimport numpy as np
import numpy

cdef double set_double(double& to_set, double value):
     to_set = value
     return to_set

cdef vector[int] convert_vector(python_vector):
     cdef vector[int] ret_vec
     for value in python_vector:
          ret_vec.push_back(value)
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
        # return m(i,j) # this doesn't work: error: ‘operator()’ not defined
        # return m.operator()(i,j) # this doesn't work: Object of type 'matrix[double]' has no attribute 'operator'
        return dereference(self.thisptr)(i,j)
    def set(self, i, j, val):
        #dereference(self.thisptr)(i,j) = val # this doesn't work: Cannot assign to or delete this
        #cdef double &intermediate = dereference(self.thisptr)(i,j) # this doesn't work: error: ‘__pyx_v_intermediate’ declared as reference but not initialized
        set_double(dereference(self.thisptr)(i,j), val)
        return dereference(self.thisptr)(i,j)
    def __repr__(self):
        return "matrix[%s, %s]" % (self.thisptr.size1(), self.thisptr.size2())

cdef matrix[double]* convert_data(np.ndarray[np.float64_t, ndim=2] data):
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
          # getters
          double get_marginal_logp()
          int get_num_views()
          c_map[int, set[int]] get_column_groups()
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
                                   vector[int] global_row_indices,
                                   vector[int] global_col_indices,
                                   int N_GRID, int SEED)
     State *new_State "new State" (matrix[double] &data,
                                   vector[int] global_row_indices,
                                   vector[int] global_col_indices,
                                   c_map[int, c_map[string, double]] hypers_m,
                                   vector[vector[int]] column_partition,
                                   double column_crp_alpha,
                                   vector[vector[vector[int]]] row_partition_v,
                                   vector[double] row_crp_alpha_v,
                                   int N_GRID, int SEED)
     void del_State "delete" (State *s)

cdef class p_State:
    cdef State *thisptr
    cdef matrix[double] *dataptr
    cdef vector[int] gri
    cdef vector[int] gci
    def __cinit__(self, data,
                  global_row_indices=None, global_col_indices=None,
                  hypers_m=None,
                  column_partition=None, column_crp_alpha=None,
                  row_partition_v=None, row_crp_alpha_v=None,
                  N_GRID=31, SEED=0):
         if global_row_indices is None:
              global_row_indices = range(len(data))
         if global_col_indices is None:
              global_col_indices = range(len(data[0]))
         self.dataptr = convert_data(data)
         self.gri = convert_vector(global_row_indices)
         self.gci = convert_vector(global_col_indices)
         if hypers_m is None:
              self.thisptr = new_State(dereference(self.dataptr),
                                       self.gri, self.gci,
                                       N_GRID, SEED)
         else:
              self.thisptr = new_State(dereference(self.dataptr),
                                       self.gri, self.gci,
                                       hypers_m,
                                       column_partition, column_crp_alpha,
                                       row_partition_v, row_crp_alpha_v,
                                       N_GRID, SEED)
    def __dealloc__(self):
        del_matrix(self.dataptr)
        del_State(self.thisptr)
    def __repr__(self):
        return "State[%s, %s]" % (self.dataptr.size1(), self.dataptr.size2())
    #
    # getters
    def get_column_groups(self):
        return self.thisptr.get_column_groups()
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
          return []
    def get_column_component_suffstats_i(self, view_idx):
          return self.thisptr.get_column_component_suffstats_i(view_idx)
    def get_view_state_i(self, view_idx):
          row_partition_model = self.get_row_partition_model_i(view_idx)
          column_names = self.get_column_names_i(view_idx)
          column_component_suffstats = self.get_column_component_suffstats_i(
                view_idx)
          view_state_i = dict()
          view_state_i['row_partition_model'] = row_partition_model
          view_state_i['column_names'] = column_names
          view_state_i['column_component_suffstats'] = column_component_suffstats
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

def indicator_list_to_list_of_list(indicator_list):
     list_of_list = []
     num_clusters = max(indicator_list) + 1
     import matplotlib.mlab
     import numpy
     for cluster_idx in range(num_clusters):
          which_rows = numpy.array(indicator_list)==cluster_idx
          list_of_list.append(matplotlib.mlab.find(which_rows))
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
     column_crp_alpha = numpy.exp(X_L['column_partition']['hypers']['log_alpha'])
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
