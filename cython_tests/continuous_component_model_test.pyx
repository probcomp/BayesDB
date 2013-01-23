from libcpp.vector cimport vector
from libcpp.string cimport string as cpp_string
from libcpp.map cimport map
from libcpp.pair cimport pair
from cython.operator import dereference
from cython.operator import preincrement

cdef map[cpp_string, double] string_double_map

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
        double insert_element(double element)
        double remove_element(double element)
        double incorporate_hyper_update()
        double calc_marginal_logp()
        double calc_element_predictive_logp(double element)
     ContinuousComponentModel *new_ContinuousComponentModel "new ContinuousComponentModel" (map[cpp_string, double] &in_hypers)
     void del_ContinuousComponentModel "delete" (ContinuousComponentModel *ccm)

cdef class p_ContinuousComponentModel:
    cdef ContinuousComponentModel *thisptr
    def __cinit__(self, in_map):
          set_string_double_map(in_map)
          self.thisptr = new_ContinuousComponentModel(string_double_map)
    def __dealloc__(self):
        del_ContinuousComponentModel(self.thisptr)
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
