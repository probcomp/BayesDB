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
    """A simple interface to the Cython-wrapped C++ engine

    LocalEngine holds no state other than a seed generator.
    Methods use resources on the local machine.

    """

    def __init__(self, seed=0):
        """Initialize a LocalEngine

        This is really just setting the initial seed to be used for
        initializing CrossCat states.  Seeds are generated sequentially

        """
        super(LocalEngine, self).__init__(seed=seed)

    def initialize(self, M_c, M_r, T, initialization='from_the_prior'):
        """Sample a latent state from prior

        :param M_c: The column metadata
        :type M_c: dict
        :param M_r: The row metadata
        :type M_r: dict
        :param T: The data table in mapped representation (all floats)
        :type T: list of lists
        :returns: X_L, X_D -- the latent state

        """

        # FIXME: why is M_r passed?
        SEED = self.get_next_seed()
        X_L, X_D = _do_initialize(M_c, M_r, T, initialization, SEED)
        return X_L, X_D

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        """Evolve the latent state by running transition kernels

        :param M_c: The column metadata
        :type M_c: dict
        :param T: The data table in mapped representation (all floats)
        :type T: list of lists
        :param X_L: the latent variables associated with the latent state
        :type X_L: dict
        :param X_D: the particular cluster assignments of each row in each view
        :type X_D: list of lists
        :param kernel_list: names of the transition kernels to run
        :type kernel_list: list of strings
        :param n_steps: the number of times to run each transition kernel
        :type n_steps: int
        :param c: the (global) column indices to run transitions on
        :type c: list of ints
        :param r: the (global) row indices to run transitions on
        :type r: list of ints
        :param max_iterations: the maximum number of times ot run each transition
                               kernel. Applicable only if max_time != -1.
        :type max_iterations: int
        :param max_time: the maximum amount of time (seconds) to run transitions
                         for before stopping to return progress
        :type max_time: float
        :returns: X_L, X_D -- the evolved latent state

        """

        SEED = self.get_next_seed()
        X_L_prime, X_D_prime = _do_analyze(M_c, T, X_L, X_D,
                                           kernel_list, n_steps, c, r,
                                           max_iterations, max_time,
                                           SEED)
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        """Sample values from the predictive distribution of the given latent state

        :param M_c: The column metadata
        :type M_c: dict
        :param X_L: the latent variables associated with the latent state
        :type X_L: dict
        :param X_D: the particular cluster assignments of each row in each view
        :type X_D: list of lists
        :param Y: A list of constraints to apply when sampling.  Each constraint
                  is a triplet of (r, d, v): r is the row index, d is the column
                  index and v is the value of the constraint
        :type Y: list of lists
        :param Q: A list of values to sample.  Each value is doublet of (r, d):
                  r is the row index, di is the column index
        :type Q: list of lists
        :param n: the number of samples to draw
        :type n: int
        :returns: list of floats -- samples in the same order specified by Q

        """
        get_next_seed = self.get_next_seed
        samples = _do_simple_predictive_sample(M_c, X_L, X_D, Y, Q, n, get_next_seed)
        return samples

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q, epsilon=0.001):
        """Calculate the probability of a cell taking a value within epsilon of 
        the specified values given a latent state

        :param M_c: The column metadata
        :type M_c: dict
        :param X_L: the latent variables associated with the latent state
        :type X_L: dict
        :param X_D: the particular cluster assignments of each row in each view
        :type X_D: list of lists
        :param Y: A list of constraints to apply when sampling.  Each constraint
                  is a triplet of (r, d, v): r is the row index, d is the column
                  index and v is the value of the constraint
        :type Y: list of lists
        :param Q: A list of values to sample.  Each value is doublet of (r, d):
                  r is the row index, di is the column index
        :type Q: list of lists
        :param epsilon: the window around the specified value to take the delta
                        in cdf of
        :type epsilon: float
        :returns: list of floats -- probabilities of the values specified by Q

        """
        return su.simple_predictive_probability(M_c, X_L, X_D, Y, Q, epsilon)

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        """Impute values from the predictive distribution of the given latent state

        :param M_c: The column metadata
        :type M_c: dict
        :param X_L: the latent variables associated with the latent state
        :type X_L: dict
        :param X_D: the particular cluster assignments of each row in each view
        :type X_D: list of lists
        :param Y: A list of constraints to apply when sampling.  Each constraint
                  is a triplet of (r, d, v): r is the row index, d is the column
                  index and v is the value of the constraint
        :type Y: list of lists
        :param Q: A list of values to sample.  Each value is doublet of (r, d):
                  r is the row index, di is the column index
        :type Q: list of lists
        :param n: the number of samples to use in the imputation
        :type n: int
        :returns: list of floats -- imputed values in the same order as
                  specified by Q

        """
        e = su.impute(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        return e

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        """Impute values and confidence of the value from the predictive
        distribution of the given latent state

        :param M_c: The column metadata
        :type M_c: dict
        :param X_L: the latent variables associated with the latent state
        :type X_L: dict
        :param X_D: the particular cluster assignments of each row in each view
        :type X_D: list of lists
        :param Y: A list of constraints to apply when sampling.  Each constraint
                  is a triplet of (r, d, v): r is the row index, d is the column
                  index and v is the value of the constraint
        :type Y: list of lists
        :param Q: A list of values to sample.  Each value is doublet of (r, d):
                  r is the row index, di is the column index
        :type Q: list of lists
        :param n: the number of samples to use in the imputation
        :type n: int
        :returns: list of lists -- list of (value, confidence) tuples in the
                  same order as specified by Q

        """
        if isinstance(X_L, (list, tuple)):
            assert isinstance(X_D, (list, tuple))
            # TODO: multistate impute doesn't exist yet
            #e,confidence = su.impute_and_confidence_multistate(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
            e,confidence = su.impute_and_confidence(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        else:
            e,confidence = su.impute_and_confidence(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        return (e,confidence)


def _do_initialize(M_c, M_r, T, initialization, SEED):
    p_State = State.p_State(M_c, T, initialization=initialization, SEED=SEED)
    X_L = p_State.get_X_L()
    X_D = p_State.get_X_D()
    return X_L, X_D

def _do_analyze(M_c, T, X_L, X_D, kernel_list, n_steps, c, r,
               max_iterations, max_time, SEED):
    p_State = State.p_State(M_c, T, X_L, X_D, SEED=SEED)
    p_State.transition(kernel_list, n_steps, c, r,
                       max_iterations, max_time)
    X_L_prime = p_State.get_X_L()
    X_D_prime = p_State.get_X_D()
    return X_L_prime, X_D_prime

def _do_simple_predictive_sample(M_c, X_L, X_D, Y, Q, n, get_next_seed):
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
