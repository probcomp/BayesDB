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
import inspect
#
import tabular_predDB.python_utils.general_utils as gu


class EngineTemplate(object):

    def __init__(self, seed=0):
        self.seed_generator = gu.int_generator(seed)

    def get_next_seed(self):
        return self.seed_generator.next()

    def initialize(self, M_c, M_r, T, initialization='from_the_prior'):
        M_c, M_r, X_L, X_D = dict(), dict(), dict(), []
        return X_L, X_D

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        X_L_prime, X_D_prime = dict(), []
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        samples = []
        return samples

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q, n):
        p = None
        return p

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        e = None
        return e

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        e, confidence = None, None
        return e, confidence

    def conditional_entropy(M_c, X_L, X_D, d_given, d_target,
                            n=None, max_time=None):
        e = None
        return e

    def predictively_related(self, M_c, X_L, X_D, d,
                                           n=None, max_time=None):
        m = []
        return m

    def contextual_structural_similarity(self, X_D, r, d):
        s = []
        return s

    def structural_similarity(self, X_D, r):
        s = []
        return s

    def structural_anomalousness_columns(self, X_D):
        a = []
        return a

    def structural_anomalousness_rows(self, X_D):
        a = []
        return a

    def predictive_anomalousness(self, M_c, X_L, X_D, T, q, n):
        a = []
        return a

