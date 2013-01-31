import inspect
#
import numpy
#
import cython.State as State


class Engine(object):

    def __init__(self):
        self.seed = 0

    def initialize(self, M_c, M_r, T, i):
        p_State = State.p_State(numpy.array(T))
        X_L = p_State.get_X_L()
        X_D = p_State.get_X_D()
        return M_c, M_r, X_L, X_D

    def analyze(self, M_c, T, X_L, X_D, kernel_list, n_steps, c, r,
                max_iterations, max_time):
        constructor_args = \
            State.transform_latent_state_to_constructor_args(X_L, X_D)
        p_State = State.p_State(numpy.array(T), **constructor_args)
        for idx in range(n_steps):
            p_State.transition()
        #
        X_L_prime = p_State.get_X_L()
        X_D_prime = p_State.get_X_D()
        return X_L_prime, X_D_prime

    def initialize_and_analyze(self, T, n_steps, SEED=None):
        if SEED is None:
            SEED = self.seed
            self.seed += 1
        print 'initialize_and_analyze: using seed', SEED
        p_State = State.p_State(numpy.array(T), SEED=SEED)
        for idx in range(n_steps):
            print "transitioning"
            p_State.transition()
        X_L_prime = p_State.get_X_L()
        X_D_prime = p_State.get_X_D()
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, q):
        x = []
        return x

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q, n):
        p = None
        return p

    def impute(self, M_c, X_L, X_D, Y, q, n):
        SEED = self.seed
        self.seed += 1
        random_state = numpy.random.RandomState(SEED)
        #
        e = random_state.normal(size=len(q)).to_list()
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
