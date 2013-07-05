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
import tabular_predDB.cython_code.State as State
import tabular_predDB.EngineTemplate as EngineTemplate
import tabular_predDB.python_utils.sample_utils as su


class LocalEngine(EngineTemplate.EngineTemplate):

    def __init__(self, seed=0):
        super(LocalEngine, self).__init__(seed=seed)

    def initialize(self, M_c, M_r, T, initialization='from_the_prior'):
        # FIXME: why is M_r passed?
        SEED = self.get_next_seed()
        X_L, X_D = do_initialize(M_c, M_r, T, initialization, SEED)
        return M_c, M_r, X_L, X_D

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        SEED = self.get_next_seed()
        X_L_prime, X_D_prime = do_analyze(M_c, T, X_L, X_D,
                                           kernel_list, n_steps, c, r,
                                           max_iterations, max_time,
                                           SEED)
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        get_next_seed = self.get_next_seed
        samples = do_simple_predictive_sample(M_c, X_L, X_D, Y, Q, n, get_next_seed)
        return samples

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        e = su.impute(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        return e

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        if isinstance(X_L, (list, tuple)):
            assert isinstance(X_D, (list, tuple))
            # TODO: multistate impute doesn't exist yet
            e,confidence = su.impute_and_confidence_multistate(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        else:
            e,confidence = su.impute_and_confidence(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        return (e,confidence)


def do_initialize(M_c, M_r, T, initialization, SEED):
    p_State = State.p_State(M_c, T, initialization=initialization, SEED=SEED)
    X_L = p_State.get_X_L()
    X_D = p_State.get_X_D()
    return X_L, X_D

def do_analyze(M_c, T, X_L, X_D, kernel_list, n_steps, c, r,
               max_iterations, max_time, SEED):
    p_State = State.p_State(M_c, T, X_L, X_D, SEED=SEED)
    p_State.transition(kernel_list, n_steps, c, r,
                       max_iterations, max_time)
    X_L_prime = p_State.get_X_L()
    X_D_prime = p_State.get_X_D()
    return X_L_prime, X_D_prime

def do_simple_predictive_sample(M_c, X_L, X_D, Y, Q, n, get_next_seed):
    is_multistate = su.get_is_multistate(X_L, X_D)
    if is_multistate:
        samples = su.simple_predictive_sample_multistate(M_c, X_L, X_D, Y, Q,
                                                         get_next_seed, n)
    else:
        samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q,
                                              get_next_seed, n)
    return samples


if __name__ == '__main__':
    le = LocalEngine(seed=10)
