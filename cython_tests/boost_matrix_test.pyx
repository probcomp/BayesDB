from cython.operator import dereference
from cython.operator cimport dereference as cderef
from cython.operator import preincrement

cdef extern from "<boost/numeric/ublas/matrix.hpp>" namespace "boost::numeric::ublas":
    cdef cppclass matrix[double]:
        void clear()
        int size1()
        int size2()
        double& operator()(int i, int j)
    matrix[double] *new_matrix "new boost::numeric::ublas::matrix<double>" (int i, int j)
    void del_matrix "delete" (matrix *m)

cdef double set_double(double& to_set, double value):
     to_set = value
     return to_set

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
