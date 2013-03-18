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
    query_row = Q[0][0]
    query_columns = [query[1] for query in Q]
    # enforce all same row
    assert(all([query[0]==query_row for query in Q]))
    # enforce observed column
    assert(all([query_column<num_cols for query_column in query_columns]))
    is_observed_row = query_row < num_rows
    x = []
    if not is_observed_row:
        SEED = get_next_seed()
        x = simple_predictive_sample_unobserved(
            M_c, X_L, X_D, Y, query_columns, SEED)
    else:
        SEED = get_next_seed()
        x = simple_predictive_sample_observed(
            M_c, X_L, X_D, query_row, query_columns, SEED)
    return x

def simple_predictive_sample_observed(M_c, X_L, X_D, which_row,
                                      which_columns, SEED):
    get_which_view = lambda which_column: \
        X_L['column_partition']['assignments'][which_column]
    column_to_view = dict()
    for which_column in which_columns:
        column_to_view[which_column] = get_which_view(which_column)
    #
    view_to_cluster_model = dict()
    for which_view in list(set(column_to_view.values())):
        which_cluster = X_D[which_view][which_row]
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, which_view,
                                                      which_cluster)
        view_to_cluster_model[which_view] = cluster_model
    #
    draws = []
    for which_column in which_columns:
        which_view = column_to_view[which_column]
        cluster_model = view_to_cluster_model[which_view]
        component_model = cluster_model[which_column]
        draw = component_model.get_draw(SEED)
        draws.append(draw)
    return draws

def names_to_global_indices(column_names, M_c):
    name_to_idx = M_c['name_to_idx']
    # FIXME: str(column_name) is hack
    return [name_to_idx[str(column_name)] for column_name in column_names]

def extract_view_column_info(M_c, X_L, view_idx):
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
    zipped_column_info = zip(column_metadata, column_hypers,
                             column_component_suffstats)
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

def get_component_model_constructor(modeltype):
    if modeltype == 'normal_inverse_gamma':
        component_model_constructor = CCM.p_ContinuousComponentModel
    elif modeltype == 'symmetric_dirichlet_discrete':
        component_model_constructor = MCM.p_MultinomialComponentModel
    else:
        assert False, \
            "get_model_constructor: unknown modeltype: %s" % modeltype
    return component_model_constructor
    
def create_component_model(column_metadata, column_hypers, count, suffstats):
    modeltype = column_metadata['modeltype']
    component_model_constructor = get_component_model_constructor(modeltype)
    # FIXME: this is a hack
    if modeltype == 'symmetric_dirichlet_discrete' and suffstats is not None:
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
                                                 column_hypers, None, dict())
        cluster_component_models[global_column_idx] = component_model
    return cluster_component_models

def create_cluster_models(M_c, X_L, view_idx, which_columns=None):
    zipped_column_info, row_partition_model = extract_view_column_info(
        M_c, X_L, view_idx)
    if which_columns is not None:
        zipped_column_info = get_column_info_subset(
            zipped_column_info, which_columns)
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
        if constraint_index in cluster_model:
            component_model = cluster_model[constraint_index]
            logp += component_model.calc_element_predictive_logp(
                constraint_value)
    return logp

def determine_cluster_data_logps(M_c, X_L, X_D, Y, view_idx):
    logps = []
    if Y is not None:
        constraint_columns = [constraint.index for constraint in Y]
        cluster_models = create_cluster_models(M_c, X_L, view_idx,
                                               constraint_columns)
        for cluster_model in cluster_models:
            logp = determine_cluster_data_logp(cluster_model, Y)
            logps.append(logp)
    else:
        view_state_i = X_L['view_state'][view_idx]
        num_clusters = len(view_state_i['row_partition_model']['counts'])
        logps = [0 for cluster_idx in range(num_clusters)]
        logps.append(0)
    return logps

def determine_cluster_crp_logps(view_state_i):
    counts = view_state_i['row_partition_model']['counts']
    log_alpha = view_state_i['row_partition_model']['hypers']['log_alpha']
    alpha = numpy.exp(log_alpha)
    counts_appended = numpy.append(counts, alpha)
    sum_counts_appended = sum(counts_appended)
    logps = numpy.log(counts_appended / float(sum_counts_appended))
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

def sample_from_cluster(cluster_model, random_state):
    sample = []
    for column_index in sorted(cluster_model.keys()):
        component_model = cluster_model[column_index]
        seed_i = random_state.randint(32767) # sys.maxint)
        sample_i = component_model.get_draw(seed_i)
        sample.append(sample_i)
    return sample

def create_cluster_model_from_X_L(M_c, X_L, view_idx, cluster_idx):
    zipped_column_info, row_partition_model = extract_view_column_info(
        M_c, X_L, view_idx)
    num_clusters = len(row_partition_model['counts'])
    if(cluster_idx==num_clusters):
        # drew a new cluster
        cluster_model = create_empty_cluster_model(zipped_column_info)
    else:
        cluster_model = create_cluster_model(
            zipped_column_info, row_partition_model, cluster_idx
            )
    return cluster_model

def determine_cluster_view_logps(M_c, X_L, X_D, Y):
    get_which_view = lambda which_column: \
        X_L['column_partition']['assignments'][which_column]
    column_to_view = dict()
    for which_column in which_columns:
        column_to_view[which_column] = get_which_view(which_column)

    num_views = len(X_D)

    cluster_logps_list = []
    for view_idx in range(num_views):
        cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, view_idx)
        cluster_logps_list.append(cluster_logp)
    return cluster_view_logps

def simple_predictive_sample_unobserved(M_c, X_L, X_D, Y, which_columns,
                                        SEED):
    random_state = numpy.random.RandomState(SEED)
    num_views = len(X_D)
    #
    cluster_logps_list = []
    for view_idx in range(num_views):
        cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, view_idx)
        cluster_logps_list.append(cluster_logps)
    #
    view_cluster_draws = dict()
    for view_idx, cluster_logps in enumerate(cluster_logps_list):
        probs = numpy.exp(cluster_logps)
        probs /= sum(probs)
        draw = numpy.nonzero(numpy.random.multinomial(1, probs))[0][0]
        view_cluster_draws[view_idx] = draw
    #
    get_which_view = lambda which_column: \
        X_L['column_partition']['assignments'][which_column]
    column_to_view = dict()
    for which_column in which_columns:
        column_to_view[which_column] = get_which_view(which_column)
    view_to_cluster_model = dict()
    for which_view in list(set(column_to_view.values())):
        which_cluster = view_cluster_draws[which_view]
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, which_view,
                                                      which_cluster)
        view_to_cluster_model[which_view] = cluster_model
    #
    draws = []
    for which_column in which_columns:
        which_view = get_which_view(which_column)
        cluster_model = view_to_cluster_model[which_view]
        component_model = cluster_model[which_column]
        draw = component_model.get_draw(SEED)
        draws.append(draw)
    return draws
