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
import numpy
import tabular_predDB.cython_code.ContinuousComponentModel as CCM
import tabular_predDB.cython_code.MultinomialComponentModel as MCM
import tabular_predDB.cython_code.State as State

c_hypers = dict(r=10,nu=10,s=10,mu=10)
ccm = CCM.p_ContinuousComponentModel(c_hypers)
print "empty component model"
print ccm
#
for element in [numpy.nan, 0, 1, numpy.nan, 2]:
    print
    ccm.insert_element(element)
    print "inserted %s" % element
    print ccm

m_hypers = dict(dirichlet_alpha=10,K=3)
mcm = MCM.p_MultinomialComponentModel(m_hypers)
print "empty component model"
print mcm

for element in [numpy.nan, 0, 1, numpy.nan, 2]:
    print
    mcm.insert_element(element)
    print "inserted %s" % element
    print mcm
