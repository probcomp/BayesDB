import sys
#
import numpy
#
import tabular_predDB.cython.ContinuousComponentModel as CCM
import tabular_predDB.cython.MultinomialComponentModel as MCM


class Bunch(dict):
    def __getattr__(self, key):
        if self.has_key(key):
            return self.get(key, None)
        else:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value

Constraints = Bunch

def simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed):
    num_rows = len(X_D[0])
    num_cols = len(M_c['column_metadata'])
    which_row = Q[0][0]
    assert(all([which_tuple[0]==which_row for which_tuple in Q]))
    # FIXME: handle unobserved rows
    is_observed_row = which_row < num_rows
    assert(is_observed_row)
    x = []
    if not is_observed_row:
        SEED = get_next_seed()
        x = simple_predictive_sample_unobserved(
            M_c, X_L, X_D, Y, Q, SEED)
    else:
        for query in Q:
            which_column = query[1]
            is_observed_col = which_column < num_cols
            # FIXME: not handling unobserved columns for now
            assert(is_observed_col)
            SEED = get_next_seed()
            sample = simple_predictive_sample_observed(
                M_c, X_L, X_D, which_row, which_column, SEED)
            x.append(sample)
    return x

def simple_predictive_sample_observed_old(M_c, X_L, X_D, which_row, which_column, SEED):
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
        # FIXME: this is a hack
        component_suffstats = dict(counts=component_suffstats)
    else:
        assert False, "simple_predictive_sample_observed: unknown modeltype: %s" % modeltype
    component_model = component_model_constructor(column_hypers,
                                                  count=cluster_count,
                                                  **component_suffstats)
    draw = component_model.get_draw(SEED)
    return draw

def simple_predictive_sample_observed(M_c, X_L, X_D, which_row, which_column, SEED):
    which_view = X_L['column_partition']['assignments'][which_column]
    which_cluster = X_D[which_view][which_row]
    cluster_model = create_cluster_model_from_X_L(M_c, X_L,
                                                  which_view, which_cluster)
    component_model = cluster_model[which_column]
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

# def get_column_reordering(M_c, column_names):
#     name_to_idx = M_c['name_to_idx']
#     global_column_indices = [
#         name_to_idx[column_name]
#         for column_name in column_names
#         ]
#     column_reordering = numpy.argsort(global_column_indices)
#     return column_reordering

# def determine_constraints_in_view(view_state_i, M_c, Y):
#     Y_subset = []
#     name_to_idx = M_c['name_to_idx']
#     these_column_names = set(view_state_i['column_names'])
#     for y in Y:
#         constraint_column = y.index
#         constraint_column_name = name_to_idx[constraint_column]
#         if constraint_column_name in these_column_names:
#             Y_subset.append(y)
#     return Y_subset

# def determine_constraint_view_tuples(X_L, M_c, Y):
#     constraint_view_tuples = []
#     for view_state_i in X_L['view_state']:
#         constraints_in_view = determine_constraints_in_view(
#             view_state_i, M_c, Y)
#         constraint_view_tuple = (constraints_in_view, view_state_i)
#         constraint_view_tuples.append(constraint_view_tuple)
#     return constraint_view_tuples

def determine_cluster_crp_logps(view_state_i):
    counts = view_state_i['row_paritition_model']['counts']
    alpha = numpy.exp(view_state_i['row_paritition_model']['log_alpha'])
    counts_appended = numpy.append(counts, alpha)
    sum_counts_appended = sum(counts_appended)
    logps = numpy.log(counts_appended / float(sum_counts_appended))
    return logps

def extract_view_info(M_c, X_L, view_idx):
    view_state_i = X_L['view_state'][view_idx]
    column_names = view_state_i['column_names']
    column_component_suffstats = view_state_i['column_component_suffstats']
    # ensure view_state_i ordering matches global ordering
    global_column_indices = names_to_global_indices(column_names, M_c)
    column_metadata = numpy.array([
        M_c['column_metadata'][col_idx]
        for col_idx in global_column_indices
        ])
    column_hypers = numpy.array([
            X_L['column_hypers'][col_idx]
            for col_idx in global_column_indices
            ])
    zipped_column_info = zip(column_metadata, column_hypers, column_component_suffstats)
    zipped_column_info = dict(zip(global_column_indices, zipped_column_info))
    row_partition_model = view_state_i['row_partition_model']
    return zipped_column_info, row_partition_model

def get_column_info_subset(zipped_column_info, column_indices):
    column_info_subset = dict()
    for column_index in column_indices:
        if column_index in zipped_column_info:
            column_info_subset[column_index] = \
                zipped_column_info[column_index]
    return column_info_subset

def names_to_global_indices(column_names, M_c):
    name_to_idx = M_c['name_to_idx']
    # FIXME: str(column_name) is hack
    return [name_to_idx[str(column_name)] for column_name in column_names]

def get_component_model_constructor(modeltype):
    if modeltype == 'normal_inverse_gamma':
        component_model_constructor = CCM.p_ContinuousComponentModel
    elif modeltype == 'symmetric_dirichlet_discrete':
        component_model_constructor = MCM.p_MultinomialComponentModel
    else:
        assert False, "get_model_constructor: unknown modeltype: %s" % modeltype
    return component_model_constructor
    
def create_component_model(column_metadata, column_hypers, count, suffstats):
    modeltype = column_metadata['modeltype']
    component_model_constructor = get_component_model_constructor(modeltype)
    # FIXME: this is a hack
    if modeltype == 'symmetric_dirichlet_discrete':
        suffstats = dict(counts=suffstats)
    component_model = component_model_constructor(column_hypers, count,
                                                  **suffstats)
    return component_model

def create_cluster_model(zipped_column_info, row_partition_model,
                         cluster_idx):
    count = row_partition_model['counts'][cluster_idx]
    cluster_component_models = dict()
    for global_column_idx in zipped_column_info:
        column_metadata, column_hypers, column_component_suffstats = \
            zipped_column_info[global_column_idx]
        cluster_component_suffstats = column_component_suffstats[cluster_idx]
        component_model = create_component_model(
            column_metadata, column_hypers, count,
            cluster_component_suffstats)
        cluster_component_models[global_column_idx] = component_model
    return cluster_component_models

def create_empty_cluster_model(zipped_column_info):
    cluster_component_models = dict()
    for global_column_idx in zipped_column_info:
        column_metadata, column_hypers, column_component_suffstats = \
            zipped_column_info[global_column_idx]
        component_model = create_component_model(column_metadata,
                                                 column_hypers, None, None)
        cluster_component_models[global_column_idx] = component_model
    return cluster_component_models

def create_cluster_models(M_c, X_L, view_idx, constraints=None):
    zipped_column_info, row_partition_model = extract_view_info(
        M_c, X_L, view_idx)
    if constraints is not None:
        constraint_columns = [constraint.index for constraint in constraints]
        zipped_column_info = get_column_info_subset(
            zipped_column_info, constraint_columns)
    cluster_models = []
    for cluster_idx in range():
        cluster_model = create_cluster_model(
            zipped_column_info, row_partition_model, cluster_idx
            )
        cluster_models.append(cluster_model)
    empty_cluster_model = create_empty_cluster_model(zipped_column_info)
    cluster_models.append(empty_cluster_model)
    return cluster_models

def determine_cluster_data_logp(cluster_model, column_constraints):
    logp = 0
    for column_constraint in column_constraints:
        constraint_index = column_constraint.index
        constraint_value = column_constraint.value
        component_model = cluster_model[constraint_index]
        logp += component_model.cacl_element_predictive_logp(constraint_value)
    return logp

def determine_cluster_data_logps(M_c, X_L, X_D, Y, view_idx):
    cluster_models = create_cluster_models(M_c, X_L, view_idx, constraints=Y)
    for cluster_model in cluster_models:
        logp = determine_cluster_data_logp(cluster_model)
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

def simple_predictive_sample_unobserved(M_c, X_L, X_D, Y, which_column,
                                        SEED):
    num_views = len(X_D)
    cluster_logps_list = []
    for view_idx in range(num_views):
        cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, view_idx)
        cluster_logps_list.append(cluster_logp)
    # sample a cluster index from each view
    random_state = numpy.random.RandomState(SEED)
    sample_list = []
    for view_idx, cluster_logps in enumerate(cluster_lopgs_list):
        draw = numpy.nonzero(numpy.random.multinomial(1, cluster_logps))[0]
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, view_idx, draw)
        sample = sample_from_cluster(cluster_model)
        sample_list.append(sample)
    # FIXME: clean up and make a lookup from individual sample dictionaries
    return sample_list

def sample_from_view_cluster(M_c, X_L, X_D, Q, SEED):
    pass

