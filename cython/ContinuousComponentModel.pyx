from libcpp.vector cimport vector
from libcpp.string cimport string as cpp_string
from libcpp.map cimport map as cpp_map
from cython.operator import dereference

cdef cpp_map[cpp_string, double] string_double_map


cdef extern from "string" namespace "std":
    cdef cppclass string:
        char* c_str()
        string(char*)

cdef cpp_string get_string(in_string):
     cdef cpp_string cps = string(in_string)
     return cps

cpdef set_string_double_map(in_map):
    for key in in_map:
        string_double_map[get_string(key)] = in_map[key]

cdef extern from "ContinuousComponentModel.h":
     cdef cppclass ContinuousComponentModel:
        double score
        double get_draw(double student_t_draw)
        double get_r()
        double insert_element(double element)
        double remove_element(double element)
        double incorporate_hyper_update()
        double calc_marginal_logp()
        double calc_element_predictive_logp(double element)
     ContinuousComponentModel *new_ContinuousComponentModel "new ContinuousComponentModel" (cpp_map[cpp_string, double] &in_hypers)
     ContinuousComponentModel *new_ContinuousComponentModel "new ContinuousComponentModel" (cpp_map[cpp_string, double] &in_hypers, int COUNT, double SUM_X, double SUM_X_SQ)
     void del_ContinuousComponentModel "delete" (ContinuousComponentModel *ccm)

cdef class p_ContinuousComponentModel:
    cdef ContinuousComponentModel *thisptr
    def __cinit__(self, in_map, count=None, sum_x=None, sum_x_sq=None):
          set_string_double_map(in_map)
          if count is None:
              self.thisptr = new_ContinuousComponentModel(string_double_map)
          else:
              self.thisptr = new_ContinuousComponentModel(string_double_map,
                                                          count, sum_x, sum_x_sq)
    def __dealloc__(self):
        del_ContinuousComponentModel(self.thisptr)
    def get_draw(self, student_t_draw):
        return self.thisptr.get_draw(student_t_draw)
    def get_r(self):
        return self.thisptr.get_r()
    def insert_element(self, element):
        return self.thisptr.insert_element(element)
    def remove_element(self, element):
        return self.thisptr.remove_element(element)
    def incorporate_hyper_update(self):
        return self.thisptr.incorporate_hyper_update()
    def calc_marginal_logp(self):
        return self.thisptr.calc_marginal_logp()
    def calc_element_predictive_logp(self, element):
        return self.thisptr.calc_element_predictive_logp(element)
    def __repr__(self):
        return "ContinuousComponentModel[%s]" % (self.thisptr.calc_marginal_logp())
