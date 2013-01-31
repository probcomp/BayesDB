import inspect
#
import numpy
#
import cython.State as State
import cython.ContinuousComponentModel as CCM

class Engine(object):

    def __init__(self):
        self.seed = 0

    def get_next_seed(self):
        SEED = self.seed
        self.seed += 1
        return SEED

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
            SEED = self.get_next_seed()
        print 'initialize_and_analyze: using seed', SEED
        p_State = State.p_State(numpy.array(T), SEED=SEED)
        for idx in range(n_steps):
            print "transitioning"
            p_State.transition()
        X_L_prime = p_State.get_X_L()
        X_D_prime = p_State.get_X_D()
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, q):
        which_row = q[0]
        which_column = q[1]
        #
        num_rows = len(X_D[0])
        num_cols = len(M_c['column_metadata'])
        #
        column_hypers = X_L['column_hypers'][which_column]
        which_view = X_L['column_partition']['assignments'][which_column]
        view_state_i = X_L['view_state'][which_view]
        #
        column_name = M_c['idx_to_name'][str(which_column)]
        column_names = X_L['view_state'][which_view]['column_names']
        which_column_name = column_names.index(column_name)
        column_component_suffstats = \
            X_L['view_state'][which_view]['column_component_suffstats']
        column_component_suffstats_i = \
            column_component_suffstats[which_column_name]
        #
        x = []
        if which_row is not None:
            which_cluster = X_D[which_view][which_row]
            component_suffstats = column_component_suffstats_i[which_cluster]
            # build a suffstats object
            component_model = CCM.p_ContinuousComponentModel(column_hypers,
                                                             **component_suffstats)
            SEED = self.get_next_seed()
            print "seed is", SEED
            r = component_model.get_r()
            print "r is", r
            random_state = numpy.random.RandomState(SEED)
            standard_t_draw = random_state.standard_t(r)
            print "standard_t_draw is", standard_t_draw
            x.append(component_model.get_draw(standard_t_draw))
        else:
            pass
        return x

    def simple_predictive_probability(self, M_c, X_L, X_D, Y, Q, n):
        p = None
        return p

    def impute(self, M_c, X_L, X_D, Y, q, n):
        # FIXME: actually implement 
        # FIXME: just spitting out random normals for now 
        SEED = self.get_next_seed()
        random_state = numpy.random.RandomState(SEED)
        #
        e = random_state.normal(size=len(q)).tolist()
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
