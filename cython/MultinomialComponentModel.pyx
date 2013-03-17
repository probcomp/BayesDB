from libcpp.vector cimport vector
from libcpp.string cimport string as cpp_string
from libcpp.map cimport map as cpp_map
from cython.operator import dereference


cdef extern from "string" namespace "std":
    cdef cppclass string:
        char* c_str()
        string(char*)

cdef cpp_string get_string(in_string):
     cdef cpp_string cps = string(in_string)
     return cps

cdef set_string_double_map(cpp_map[cpp_string, double] &out_map, in_map):
    for key in in_map:
        out_map[get_string(key)] = in_map[key]

cdef extern from "MultinomialComponentModel.h":
     cdef cppclass MultinomialComponentModel:
        double score
        cpp_string to_string()
        double get_draw(int seed)
        void get_suffstats(int count_out, cpp_map[cpp_string, double] counts)
        double insert_element(double element)
        double remove_element(double element)
        double incorporate_hyper_update()
        double calc_marginal_logp()
        double calc_element_predictive_logp(double element)
     MultinomialComponentModel *new_MultinomialComponentModel "new MultinomialComponentModel" (cpp_map[cpp_string, double] &in_hypers)
     MultinomialComponentModel *new_MultinomialComponentModel "new MultinomialComponentModel" (cpp_map[cpp_string, double] &in_hypers, int COUNT, cpp_map[cpp_string, double] counts)
     void del_MultinomialComponentModel "delete" (MultinomialComponentModel *ccm)

cdef class p_MultinomialComponentModel:
    cdef MultinomialComponentModel *thisptr
    cdef cpp_map[cpp_string, double] hypers
    def __cinit__(self, in_map, count=None, counts=None):
          set_string_double_map(self.hypers, in_map)
          if count is None:
              self.thisptr = new_MultinomialComponentModel(self.hypers)
          else:
              self.thisptr = new_MultinomialComponentModel(self.hypers,
                                                          count, counts)
    def __dealloc__(self):
        del_MultinomialComponentModel(self.thisptr)
    def get_draw(self, seed):
        return self.thisptr.get_draw(seed)
    def get_suffstats(self):
        cdef int count_out
        count_out = 0
        counts = dict()
        self.thisptr.get_suffstats(count_out, counts)
        return count_out, counts
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
        return self.thisptr.to_string()
