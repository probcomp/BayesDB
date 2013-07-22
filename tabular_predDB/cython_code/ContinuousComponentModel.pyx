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

cdef extern from "ContinuousComponentModel.h":
     cdef cppclass ContinuousComponentModel:
        double score
        cpp_string to_string()
        double get_draw(int seed)
        double get_draw_constrained(int seed, vector[double] constraints)
        double get_predictive_cdf(double element, vector[double] constraints)
        double get_predictive_pdf(double element, vector[double] constraints)
        double insert_element(double element)
        double remove_element(double element)
        double incorporate_hyper_update()
        double calc_marginal_logp()
        double calc_element_predictive_logp(double element)
        double calc_element_predictive_logp_constrained(double element, vector[double] constraints)
     ContinuousComponentModel *new_ContinuousComponentModel "new ContinuousComponentModel" (cpp_map[cpp_string, double] &in_hypers)
     ContinuousComponentModel *new_ContinuousComponentModel "new ContinuousComponentModel" (cpp_map[cpp_string, double] &in_hypers, int COUNT, double SUM_X, double SUM_X_SQ)
     void del_ContinuousComponentModel "delete" (ContinuousComponentModel *ccm)

cdef class p_ContinuousComponentModel:
    cdef ContinuousComponentModel *thisptr
    cdef cpp_map[cpp_string, double] hypers
    def __cinit__(self, in_map, count=None, sum_x=None, sum_x_squared=None):
          set_string_double_map(self.hypers, in_map)
          if count is None:
              self.thisptr = new_ContinuousComponentModel(self.hypers)
          else:
              self.thisptr = new_ContinuousComponentModel(self.hypers,
                                                          count, sum_x, sum_x_squared)
    def __dealloc__(self):
        del_ContinuousComponentModel(self.thisptr)
    def get_draw(self, seed):
        return self.thisptr.get_draw(seed)
    def get_draw_constrained(self, seed, constraints):
        return self.thisptr.get_draw_constrained(seed, constraints)
    # simple predictive probability (BAX)
    def get_predictive_cdf(self, element, constraints):
        return self.thisptr.get_predictive_cdf(element, constraints)
    def get_predictive_pdf(self, element, constraints):
        return self.thisptr.get_predictive_pdf(element, constraints)
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
    def calc_element_predictive_logp_constrained(self, element,
                                                  constraints):
        return self.thisptr.calc_element_predictive_logp_constrained(
            element, constraints)
    def __repr__(self):
        return self.thisptr.to_string()
