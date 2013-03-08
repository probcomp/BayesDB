import inspect
import sys
from collections import Counter
#
import numpy
#
import cython.State as State
import cython.ContinuousComponentModel as CCM
import cython.MultinomialComponentModel as MCM

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
        # FIXME: actually pay attention to kernerl_list, max_time, etc
        for idx in range(n_steps):
            p_State.transition()
        #
        X_L_prime = p_State.get_X_L()
        X_D_prime = p_State.get_X_D()
        return X_L_prime, X_D_prime

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, q):
        x = []
        # FIXME: handle multiple queries
        assert(len(q)==1)
        for query in q:
            which_row = query[0]
            which_column = query[1]
            #
            num_rows = len(X_D[0])
            num_cols = len(M_c['column_metadata'])
            is_observed_row = which_row < num_rows
            is_observed_col = which_column < num_cols
            assert(is_observed_col)
            # FIXME: handle unobserved rows
            assert(is_observed_row)
            if is_observed_col and is_observed_row:
                SEED = self.get_next_seed()
                sample = simple_predictive_sample_observed(M_c, X_L, X_D,
                                                           which_row,
                                                           which_column,
                                                           SEED)
                x.append(sample)
            elif is_observed_col and not is_observed_row:
                SEED = self.get_next_seed()
                sample = simple_predictive_sample_unobserved(M_c, X_L, X_D,
                                                             Y,
                                                             which_column,
                                                             SEED)
                x.append(sample)
            else:
                # FIXME: not handling unobserved columns for now
                assert(False)
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

def simple_predictive_sample_observed(M_c, X_L, X_D, which_row, which_column, SEED):
    modeltype = M_c['column_metadata'][which_column]['modeltype']
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
    which_cluster = X_D[which_view][which_row]
    cluster_count = sum(numpy.array(X_D[which_view])==which_cluster)
    component_suffstats = column_component_suffstats_i[which_cluster]
    component_model_constructor = None
    if modeltype == 'normal_inverse_gamma':
        component_model_constructor = CCM.p_ContinuousComponentModel
    elif modeltype == 'symmetric_dirichlet_discrete':
        component_model_constructor = MCM.p_MultinomialComponentModel
    else:
        assert False, "simple_predictive_sample_observed: unknown modeltype: %s" % modeltype
    component_model = component_model_constructor(column_hypers,
                                                  count=cluster_count,
                                                  **component_suffstats)
    draw = component_model.get_draw(SEED)
    return draw

# determine views involved
# for each view:
#   determine probability of cluster in a view
#     crp probability
#     data probability
#   sample a cluster
#   generate all data from cluster
# join data

def determine_constraints_in_view(view_state_i, Y):
    column_names = view_state_i['column_names']
    constraint_names = intersect(column_names, get_names(Y))
    return list(constraint_names)

def determine_views_involved(M_c, X_L, X_D, Y, which_columns):
    which_views_involved = dict()
    for which_view_idx, which_view in enumerate(X_L['view_state']):
        constraint_names = determine_constraints_in_view(which_view, Y)
        if len(constraint_names) != 0:
            which_views_involved[which_view] = list(constraint_names)
    return which_views_involved

def determine_cluster_crp_logps(view_state_i):
    counts = view_state_i['row_paritition_model']['counts']
    alpha = numpy.exp(view_state_i['row_paritition_model']['log_alpha'])
    counts_appended = numpy.append(counts, alpha)
    sum_counts_appended = sum(counts_appended)
    logps = numpy.log(counts_appended / float(sum_counts_appended))
    return logps

def get_column_reordering(M_c, column_names):
    name_to_idx = M_c['name_to_idx']
    global_column_indices = [
        name_to_idx[column_name]
        for column_name in column_names
        ]
    column_reordering = numpy.argsort(global_column_indices)
    return column_reordering

def extract_view_info(M_c, X_L, view_idx):
    view_state_i = X_L['view_state'][view_idx]
    # ensure view_state_i ordering matches global ordering
    column_names = view_state_i['column_names']
    column_reordering = get_column_reordering(M_c, column_names)
    column_component_suffstats = view_state_i['column_component_suffstats']
    column_component_suffstats = numpy.array(column_component_suffstats)
    column_component_suffstats = column_component_suffstats[column_reordering]
    #
    column_partition_assignments = X_L['column_partition']['assignments']
    column_partition_assignments = numpy.array(column_partition_assignments)
    is_this_view = column_partition_assignments == view_idx
    column_metadata = numpy.array(M_c['column_metadata'])[is_this_view]
    column_hypers = numpy.array(X_L['column_hypers'])[is_this_view]
    row_partition_model = view_state_i['row_partition_model']
    #
    zipped_column_info = zip(column_metadata, column_hypers, column_component_suffstats)
    return zipped_column_info, row_partition_model

def get_component_model_constructor(modeltype):
    if modeltype == 'normal_inverse_gamma':
        component_model_constructor = CCM.p_ContinuousComponentModel
    elif modeltype == 'symmetric_dirichlet_discrete':
        component_model_constructor = MCM.p_MultinomialComponentModel
    else:
        assert False, "get_model_constructor: unknown modeltype: %s" % modeltype
    return component_model_constructor
    
def create_component_model(column_metadata, column_hypers, count=None,
                           suffstats=None):
    if suffstats is None: suffstats = dict()
    modeltype = column_metadata['modeltype']
    component_model_constructor = get_component_model_constructor(modeltype)
    component_model = component_model_constructor(column_hypers, count,
                                                  **suffstats)
    return component_model

def create_cluster_model(zipped_column_info, row_partition_model,
                         cluster_idx=-1):
    count = None
    if cluster_idx != -1:
        count = row_partition_model['counts'][cluster_idx]
    num_cols = len(zipped_column_info)
    cluster_component_models = []
    for local_column_idx in range(num_cols):
        column_metadata, column_hypers, column_component_suffstats = \
            zipped_column_info[local_column_idx]
        cluster_component_suffstats = None
        if cluster_idx != -1:
            cluster_component_suffstats = \
                column_component_suffstats[cluster_idx]
        component_model = create_component_model(
            column_metadata, column_hypers, count,
            cluster_component_suffstats)
        cluster_component_models.append(component_model)
    return cluster_component_models

def create_cluster_models(M_c, X_L, view_idx):
    zipped_column_info, row_partition_model = extract_view_info(
        M_c, X_L, view_idx)
    cluster_models = []
    for cluster_idx in range():
        cluster_model = create_cluster_model(
            zipped_column_info, row_partition_model, cluster_idx
            )
        cluster_models.append(cluster_model)
    cluster_model = create_cluster_model(
        zipped_column_info, row_partition_model, -1)
    cluster_models.append(cluster_models)
    return cluster_models

def inject_none_constraints(X_L, Y):
    column_partition_assignments = X_L['column_partition']['assignments']
    column_partition_assignments = numpy.array(column_partition_assignments)
    is_this_view = column_partition_assignments == view_idx
    global_col_indices = numpy.nonzero(is_this_view)[0]
    constraints = [None for col_inx in global_col_indices]
    for constraint in Y:
        constraints[Y.index] = Y.value
    return constraints

def determine_cluster_data_logp(cluster_model, column_constraints):
    logp = 0
    for component_model, column_constraint \
            in zip(cluster_model, column_constraints):
        if column_constraint is None: continue
        logp += component_model.cacl_element_predictive_logp(column_constraint)
    return logp

def determine_cluster_data_logps(M_c, X_L, X_D, Y, view_idx):
    cluster_models = create_cluster_models(M_c, X_L, view_idx)
    # must make column indices view local
    column_constraints = inject_non_constraints(X_L, Y)
    for cluster_model in cluster_models:
        logp = determine_cluster_data_logp(cluster_model, column_constraints)
        logps.append(logp)
    return logps

def determine_cluster_logps(M_c, X_L, X_D, Y, view_idx):
    view_state_i = X_L['view_state'][view_idx]
    cluster_crp_logps = determine_cluster_crp_logps(view_state_i)
    cluster_crp_logps = numpy.array(cluster_crp_logps)
    cluster_data_logps = determine_cluster_data_logps(M_c, X_L, X_D, Y,
                                                      view_idx)
    cluster_data_logps = numpy.array(cluster_data_logps)
    # 
    cluster_logps = cluster_crp_logps + cluster_data_logps
    return cluster_logps

def sample_from_cluster(cluster_model, SEED):
    random_state = numpy.random.RandomState(SEED)
    sample = []
    for component_model in cluster_model:
        seed_i = random_state.randint(sys.MAXINT)
        sample_i = component_model.get_draw(seed_i)
        sample.append(sample_i)
    return sample

def create_cluster_model_from_X_L(M_c, X_L, view_idx, cluster_idx):
    zipped_column_info, row_partition_model = extract_view_info(
        M_c, X_L, view_idx)
    cluster_model = create_cluster_model(
        zipped_column_info, row_partition_model, cluster_idx
        )
    return cluster_model

def sample_from_view(M_c, X_L, X_D, Y, view_idx, SEED):
    random_state = numpy.random.RandomState(SEED)
    cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, view_idx)
    draw = numpy.nonzero(numpy.random.multinomial(1, cluster_logps))[0]
    cluster_model = create_cluster_model_from_X_L(M_c, X_L, view_idx, draw)
    sample = sample_from_cluster(cluster_model)
    return sample

def simple_predictive_sample_unobserved(M_c, X_L, X_D, Y, which_column, SEED):
    modeltype = M_c['column_metadata'][which_column]['modeltype']
    column_hypers = X_L['column_hypers'][which_column]
    which_view = X_L['column_partition']['assignments'][which_column]
    view_state_i = X_L['view_state'][which_view]
    column_names = X_L['view_state'][which_view]['column_names']
    # find Y_prime = which conditions are in the same view as which_column
    constraint_names = intersect(column_names, get_names(Y))
    constraint_indices = map(lambda x: M_c['name_to_idx'][x], constraint_names)
    # create a view comprised of columns in Y_prime
    column_component_suffstats = \
        X_L['view_state'][which_view]['column_component_suffstats']
    column_component_suffstats = [
        column_component_suffstats[x]
        for x in constraint_indices
        ]
    # counts are missing from suffstats
    which_view_ids = numpy.array(X_D[which_view])
    counts_list = [Counter(data_col) for data_col in which_view_ids.T]

    # determine logp_v for memebership in each cluster
    # sample a cluster
    # create a single component_model from the selected cluster and given column
    num_clusters = len(column_component_suffstats[0])
    for which_local_column in range(len(counts_list)):
        for which_cluster in range(num_clusters):
            component_suffstats = column_component_suffstats_i[which_cluster]
            component_model = CCM.p_ContinuousComponentModel(column_hypers,
                                                             count=cluster_count,
                                                             **component_suffstats)
            # do something
