from cython.operator import dereference
from cython.operator import preincrement

cdef extern from "<boost/numeric/ublas/matrix.hpp>" namespace "boost::numeric::ublas":
    cdef cppclass matrix[double]:
        void clear()
        int size1()
        int size2()
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
    def __repr__(self):
        return "matrix[%s, %s]" % (self.thisptr.size1(), self.thisptr.size2())
