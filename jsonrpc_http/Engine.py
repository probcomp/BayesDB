import inspect
#
import tabular_predDB.cython.State as State
import tabular_predDB.python_utils.sample_utils as su


class Engine(object):

    def __init__(self):
        self.seed = 0

    def get_next_seed(self):
        SEED = self.seed
        self.seed += 1
        return SEED

    def initialize(self, M_c, M_r, T, initialization=None):
        # FIXME: why is M_r passed?
        p_State = State.p_State(M_c, T, initialization=initialization)
        X_L = p_State.get_X_L()
        X_D = p_State.get_X_D()
        return M_c, M_r, X_L, X_D

    def analyze(self, M_c, T, X_L, X_D, kernel_list, n_steps, c, r,
                max_iterations, max_time):
        p_State = State.p_State(M_c, T, X_L, X_D)
        # FIXME: actually pay attention to c, r, max_time
        p_State.transition(kernel_list, n_steps)
        X_L_prime = p_State.get_X_L()
        X_D_prime = p_State.get_X_D()
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        samples = su.simple_predictive_sample(M_c, X_L, X_D, Y, Q,
                                              self.get_next_seed, n)
        return samples

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q, n):
        p = None
        return p

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        e = su.impute(M_c, X_L, X_D, Y, Q, n, self.get_next_seed)
        return e

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

# helper functions
get_name = lambda x: getattr(x, '__name__')
get_Engine_attr = lambda x: getattr(Engine, x)
is_Engine_method_name = lambda x: inspect.ismethod(get_Engine_attr(x))
#
def get_method_names():
    return filter(is_Engine_method_name, dir(Engine))
#
def get_method_name_to_args():
    method_names = get_method_names()
    method_name_to_args = dict()
    for method_name in method_names:
        method = Engine.__dict__[method_name]
        arg_str_list = inspect.getargspec(method).args[1:]
        method_name_to_args[method_name] = arg_str_list
    return method_name_to_args
