from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.map cimport map
from libcpp.set cimport set
from cython.operator import dereference
cimport numpy as np

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
        cdef matrix[double] m = dereference(self.thisptr)
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

cdef double set_double(double& to_set, double value):
     to_set = value
     return to_set

cdef extern from "State.h":
     cdef cppclass State:
          double transition(matrix[double] data)
          double get_marginal_logp()
          map[int, set[int]] get_column_groups()
          vector[map[string, double]] get_column_hypers()
          map[string, double] get_column_partition_hypers()
          vector[int] get_column_partition_assignments()
          vector[int] get_column_partition_counts()
          void SaveResult()
     State *new_State "new State" (matrix[double] &data, vector[int] global_row_indices, vector[int] global_col_indices, int N_GRID, int SEED)
     void del_State "delete" (State *s)

cdef matrix[double]* convert_data(np.ndarray[np.float64_t, ndim=2] data):
     cdef int num_rows = data.shape[0]
     cdef int num_cols = data.shape[1]
     dataptr = new_matrix(num_rows, num_cols)
     cdef int i,j
     for i from 0 <= i < num_rows:
          for j from 0 <= j < num_cols:
               set_double(dereference(dataptr)(i,j), data[i,j])
     return dataptr

cdef vector[int] convert_vector(python_vector):
     cdef vector[int] ret_vec
     for value in python_vector:
          ret_vec.push_back(value)
     return ret_vec
	  
cdef class p_State:
    cdef State *thisptr
    cdef matrix[double] *dataptr
    cdef vector[int] gri
    cdef vector[int] gci
    def __cinit__(self, data, global_row_indices, global_col_indices, N_GRID, SEED):
          self.dataptr = convert_data(data)
          self.gri = convert_vector(global_row_indices)
          self.gci = convert_vector(global_col_indices)
          self.thisptr = new_State(dereference(self.dataptr), self.gri, self.gci, N_GRID, SEED)
    def __dealloc__(self):
        del_matrix(self.dataptr)
        del_State(self.thisptr)
    def transition(self):
        return self.thisptr.transition(dereference(self.dataptr))
    def get_marginal_logp(self):
        return self.thisptr.get_marginal_logp()
    def get_column_groups(self):
        return self.thisptr.get_column_groups()
    def get_column_hypers(self):
        return self.thisptr.get_column_hypers()
    def get_column_partition(self):
        hypers = self.thisptr.get_column_partition_hypers()
        assignments = self.thisptr.get_column_partition_assignments()
        counts = self.thisptr.get_column_partition_counts()
        return hypers, assignments, counts
    def __repr__(self):
        return "State[%s, %s]" % (self.dataptr.size1(), self.dataptr.size2())
