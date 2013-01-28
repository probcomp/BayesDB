import inspect

class FakeEngine(object):

    def initialize(self, M_c, M_r, T, i):
        X_L = {}
        X_D = [[]]
        return M_c, M_r, X_L, X_D

    def analyze(self, S, T, X_L, X_D, M_C, M_R, kernel_list,
                              n_steps, c, r, max_iterations, max_time):
        X_L_prime = {}
        X_D_prime = [[]]
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, q):
        x = []
        return x

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q,
                                                    n):
        p = None
        return p

    def impute(self, M_c, X_L, X_D, Y, q, n):
        e = []
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
get_FakeEngine_attr = lambda x: getattr(FakeEngine, x)
is_FakeEngine_method_name = lambda x: inspect.ismethod(get_FakeEngine_attr(x))
#
def get_method_names():
    return filter(is_FakeEngine_method_name, dir(FakeEngine))
#
def get_method_name_to_args():
    method_names = get_method_names()
    method_name_to_args = dict()
    for method_name in method_names:
        method = FakeEngine.__dict__[method_name]
        arg_str_list = inspect.getargspec(method).args[1:]
        method_name_to_args[method_name] = arg_str_list
    return method_name_to_args
