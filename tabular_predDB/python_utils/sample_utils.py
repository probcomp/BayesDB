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
import sys
import copy
import math

import pdb

from collections import Counter
#
from scipy.misc import logsumexp
import numpy
#
import tabular_predDB.cython_code.ContinuousComponentModel as CCM
import tabular_predDB.cython_code.MultinomialComponentModel as MCM
import tabular_predDB.python_utils.general_utils as gu

class Bunch(dict):
    def __getattr__(self, key):
        if self.has_key(key):
            return self.get(key, None)
        else:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value

Constraints = Bunch


def is_discrete(M_c, which_column):
    model_type = M_c['column_metadata'][which_column]['modeltype']
    lookup = dict( 
        normal_inverse_gamma=False,
        symmetric_dirichlet_discrete=True,
    )
    return lookup[model_type]


# simple_predictive_probability_density code is hacked from simple_predictive_probability
# code. The dfference is that it returns log(pdf) for Normal Inverse-Gamma
# rather than log(cdf(b)-cdf(a))
def simple_predictive_probability_density(M_c, X_L, X_D, Y, Q):
    num_rows = len(X_D[0])
    num_cols = len(M_c['column_metadata'])
    query_row = Q[0][0]
    query_columns = [query[1] for query in Q]
    elements = [query[2] for query in Q]
    # enforce query rows all same row
    assert(all([query[0]==query_row for query in Q]))
    # enforce query columns observed column
    assert(all([query_column<num_cols for query_column in query_columns]))
    is_observed_row = query_row < num_rows

    x = []

    if not is_observed_row:
        x = simple_predictive_probability_density_unobserved(
            M_c, X_L, X_D, Y, query_row, query_columns, elements)
        
    else:
        x = simple_predictive_probability_density_observed(
            M_c, X_L, X_D, Y, query_row, query_columns, elements)    

    return x


def simple_predictive_probability_density_observed(M_c, X_L, X_D, Y, which_row,
                                      which_columns, elements):
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
    
    Ps = numpy.zeros(len(which_columns)) 

    q = 0 # query index
    for which_column in which_columns:
        which_view = column_to_view[which_column]
        cluster_model = view_to_cluster_model[which_view]
        component_model = cluster_model[which_column]
        draw_constraints = get_draw_constraints(X_L, X_D, Y,which_row, which_column)

        is_discrete_variable = is_discrete(M_c, which_column)

        if not is_discrete_variable:
            p_x = component_model.get_predictive_pdf(elements[q],draw_constraints)
            logp = p_x
        elif is_discrete_variable:
            logp = component_model.get_predictive_probability(elements[q],draw_constraints)
        else:
            sys.err('error: simple_predictive_probability_density_observed: Could not determine discreteness')
        
        Ps[q] = logp
        q += 1

    ans = Ps
    
    return ans

def simple_predictive_probability_density_unobserved(M_c, X_L, X_D, Y, query_row, query_columns, elements):

    n_queries = len(query_columns)

    answer = numpy.zeros(n_queries)
    answers = numpy.array([])

    for n in range(n_queries):
        # figure out what kind of model we are dealing with 
        is_discrete_variable = is_discrete(M_c, query_columns[n])

        if not is_discrete_variable:
            answer[n] = simple_predictive_probability_density_unobserved_continuous(M_c, X_L, X_D, Y, query_row, query_columns[n], elements[n])
        elif is_discrete_variable:
            answer[n] = simple_predictive_probability_unobserved_discrete(M_c, X_L, X_D, Y, query_row, query_columns[n], elements[n])
        else:
            sys.exit("error: simple_predictive_probability__density_unobserved: Undefined model type.");

    return answer

def simple_predictive_probability_density_unobserved_continuous(M_c, X_L, X_D, Y, query_row,query_column, element):

    # get the view to which this column is assigned
    view_idx = X_L['column_partition']['assignments'][query_column]
    # get the logps for all the clusters (plus a new one) in this view
    cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, query_row, view_idx)

    x = element
    
    answers = numpy.zeros(len(cluster_logps))

    # cluster_logps should logsumexp to log(1)
    assert(numpy.abs(logsumexp(cluster_logps)) < .0000001)

    # enumerate over the clusters
    for cluster_idx in range(len(cluster_logps)):

        # get the cluster model for this cluster
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, view_idx, cluster_idx)
        # get the specific cluster model for this column
        component_model = cluster_model[query_column]
        # construct draw conataints
        draw_constraints = get_draw_constraints(X_L, X_D, Y, query_row, query_column)

        # return the PDF value (exp)
        p_x = component_model.get_predictive_pdf(x, draw_constraints)
        
        try:
            answers[cluster_idx] = p_x+cluster_logps[cluster_idx]
        except ValueError:
            answers[cluster_idx] = float('-inf')

    answer = logsumexp(answers)
 
    return answer


# Q is a list of three element tuples where each typle, (r,c,x) is contains a
# row, r; a column, c; and a value x. The contraints, Y follow an indentical format.
# Epsilon is the interval over which to evaluate the probability.
# Returns a numpy array where each entry, A[i] is the probability for query i given
# the contraints in Y.
def simple_predictive_probability(M_c, X_L, X_D, Y, Q, epsilon=.001):
    num_rows = len(X_D[0])
    num_cols = len(M_c['column_metadata'])
    query_row = Q[0][0]
    query_columns = [query[1] for query in Q]
    elements = [query[2] for query in Q]
    # enforce query rows all same row
    assert(all([query[0]==query_row for query in Q]))
    # enforce query columns observed column
    assert(all([query_column<num_cols for query_column in query_columns]))
    is_observed_row = query_row < num_rows

    x = []

    if not is_observed_row:
        x = simple_predictive_probability_unobserved(
            M_c, X_L, X_D, Y, query_row, query_columns, elements, epsilon=epsilon)
    else:
        x = simple_predictive_probability_observed(
            M_c, X_L, X_D, Y, query_row, query_columns, elements, epsilon=epsilon)    

    return x


def simple_predictive_probability_observed(M_c, X_L, X_D, Y, which_row,
                                      which_columns, elements, epsilon=.001):
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
    
    Ps = numpy.zeros(len(which_columns)) 

    q = 0 # query index
    for which_column in which_columns:
        which_view = column_to_view[which_column]
        cluster_model = view_to_cluster_model[which_view]
        component_model = cluster_model[which_column]
        draw_constraints = get_draw_constraints(X_L, X_D, Y,which_row, which_column)

        is_discrete_variable = is_discrete(M_c, which_column)

        if not is_discrete_variable:
            a = elements[q]-epsilon
            b = elements[q]+epsilon
            p_a = component_model.get_predictive_cdf(a,draw_constraints)
            p_b = component_model.get_predictive_cdf(b,draw_constraints)
            try:
                logp = math.log(p_b-p_a)
            except ValueError:
                logp = float('-inf')
        elif is_discrete_variable:
            logp = component_model.calc_element_predictive_logp_constrained(elements[q],draw_constraints)
        else:
            sys.exit("error: simple_predictive_probability_observed: Undefined model type.");
       
        Ps[q] = logp
        q += 1

    ans = Ps
    
    return ans
def simple_predictive_probability_unobserved(M_c, X_L, X_D, Y, query_row, query_columns, elements, epsilon=.001):

    n_queries = len(query_columns)

    answer = numpy.zeros(n_queries)

    for n in range(n_queries):
        # figure out what kind of model we are dealing with 
        is_discrete_variable = is_discrete(M_c, query_columns[n])

        if not is_discrete_variable:
            answer[n] = simple_predictive_probability_unobserved_continuous(M_c, X_L, X_D, Y, query_row, query_columns[n], elements[n],epsilon=epsilon)
        elif is_discrete_variable:
            answer[n] = simple_predictive_probability_unobserved_discrete(M_c, X_L, X_D, Y, query_row, query_columns[n], elements[n])
        else:
            sys.exit("error: simple_predictive_probability_unobserved: Undefined model type.");

    return answer

def simple_predictive_probability_unobserved_continuous(M_c, X_L, X_D, Y, query_row,query_column, element, epsilon=.001):
    # TODO: Add user-defined epsilon value?

    # get the view to which this column is assigned
    view_idx = X_L['column_partition']['assignments'][query_column]
    # get the logps for all the clusters (plus a new one) in this view
    cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, query_row, view_idx)

    # cluster_logps should logsumexp to log(1)
    assert(numpy.abs(logsumexp(cluster_logps)) < .0000001)

    # we calculate a small portion of the integral using the CDF (student's t). 
    # CDF(b) - CDF(a)
    x = element
    a = x-epsilon
    b = x+epsilon
    
    answers = numpy.zeros(len(cluster_logps))

    # enumerate over the clusters
    for cluster_idx in range(len(cluster_logps)):

        # get the cluster model for this cluster
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, view_idx, cluster_idx)
        # get the specific cluster model for this column
        component_model = cluster_model[query_column]
        # construct draw constraints
        draw_constraints = get_draw_constraints(X_L, X_D, Y, query_row, query_column)

        # return the CDF value (exp)
        p_b = component_model.get_predictive_cdf(b, draw_constraints)
        p_a = component_model.get_predictive_cdf(a, draw_constraints)

        try:
            answers[cluster_idx] = math.log(p_b-p_a)+cluster_logps[cluster_idx]
        except ValueError:
            answers[cluster_idx] = float('-inf')

    answer = logsumexp(answers)

    return answer

def simple_predictive_probability_unobserved_discrete(M_c, X_L, X_D, Y, query_row,
                                        query_column, element):
    
    # get the view to which this column is assigned
    view_idx = X_L['column_partition']['assignments'][query_column]
    # get the logps for all the clusters (plus a new one) in this view
    cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, query_row, view_idx)

    # cluster_logps should logsumexp to log(1)
    assert(numpy.abs(logsumexp(cluster_logps)) < .0000001)

    x = element

    answers = numpy.zeros(len(cluster_logps))

    for cluster_idx in range(len(cluster_logps)):

        # get the cluster model for this cluster
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, view_idx, cluster_idx)
        # get the specific cluster model for this column
        component_model = cluster_model[query_column]
        # construct draw conataints
        draw_constraints = get_draw_constraints(X_L, X_D, Y, query_row, query_column)

        px = component_model.calc_element_predictive_logp_constrained(x, draw_constraints)

        answers[cluster_idx] = px+cluster_logps[cluster_idx]

    answer = logsumexp(answers);
    
    return answer

################################################################################
################################################################################

def simple_predictive_sample(M_c, X_L, X_D, Y, Q, get_next_seed, n=1):
    num_rows = len(X_D[0])
    num_cols = len(M_c['column_metadata'])
    query_row = Q[0][0]
    query_columns = [query[1] for query in Q]
    # enforce query rows all same row
    assert(all([query[0]==query_row for query in Q]))
    # enforce query columns observed column
    assert(all([query_column<num_cols for query_column in query_columns]))
    is_observed_row = query_row < num_rows
    x = []
    if not is_observed_row:
        x = simple_predictive_sample_unobserved(
            M_c, X_L, X_D, Y, query_row, query_columns, get_next_seed, n)
    else:
        x = simple_predictive_sample_observed(
            M_c, X_L, X_D, Y, query_row, query_columns, get_next_seed, n)    
    # # more modular logic
    # observed_view_cluster_tuples = ()
    # if is_observed_row:
    #     observed_view_cluster_tuples = get_view_cluster_tuple(
    #         M_c, X_L, X_D, query_row)
    #     observed_view_cluster_tuples = [observed_view_cluster_tuples] * n
    # else:
    #     view_cluster_logps = determine_view_cluster_logps(
    #         M_c, X_L, X_D, Y, query_row)
    #     observed_view_cluster_tuples = \
    #         sample_view_cluster_tuples_from_logp(view_cluster_logps, n)
    # x = draw_from_view_cluster_tuples(M_c, X_L, X_D, Y,
    #                                   observed_view_cluster_tuples)
    return x

def simple_predictive_sample_multistate(M_c, X_L_list, X_D_list, Y, Q,
                                        get_next_seed, n=1):
    num_states = len(X_L_list)
    assert(num_states==len(X_D_list))
    n_from_each = n / num_states
    n_sampled = n % num_states
    random_state = numpy.random.RandomState(get_next_seed())
    which_sampled = random_state.permutation(xrange(num_states))[:n_sampled]
    which_sampled = set(which_sampled)
    x = []
    for state_idx, (X_L, X_D) in enumerate(zip(X_L_list, X_D_list)):
        this_n = n_from_each
        if state_idx in which_sampled:
            this_n += 1
        this_x = simple_predictive_sample(M_c, X_L, X_D, Y, Q,
                                          get_next_seed, this_n)
        x.extend(this_x)
    return x

def simple_predictive_sample_observed(M_c, X_L, X_D, Y, which_row,
                                      which_columns, get_next_seed, n=1):
    get_which_view = lambda which_column: \
        X_L['column_partition']['assignments'][which_column]
    column_to_view = dict()
    # get the views to which each column is assigned
    for which_column in which_columns:
        column_to_view[which_column] = get_which_view(which_column)
    #
    view_to_cluster_model = dict()
    for which_view in list(set(column_to_view.values())):
        # which calegory in this view
        which_cluster = X_D[which_view][which_row]
        # pull the suffstats, hypers, and marignal logP's for clusters
        cluster_model = create_cluster_model_from_X_L(M_c, X_L, which_view,
                                                      which_cluster)
        # store
        view_to_cluster_model[which_view] = cluster_model
    #
    samples_list = []
    for sample_idx in range(n):
        this_sample_draws = []
        for which_column in which_columns:
            # get the view to which this column is assigned
            which_view = column_to_view[which_column]
            # get the cluster model (suffstats, hypers, etc)
            cluster_model = view_to_cluster_model[which_view]
            # get the component model for this column
            component_model = cluster_model[which_column]
            # ?
            draw_constraints = get_draw_constraints(X_L, X_D, Y,
                                                    which_row, which_column)
            # get a random int for seeding the rng
            SEED = get_next_seed()
            # draw
            draw = component_model.get_draw_constrained(SEED,
                                                        draw_constraints)            
            this_sample_draws.append(draw)
        samples_list.append(this_sample_draws)
    return samples_list

def names_to_global_indices(column_names, M_c):
    name_to_idx = M_c['name_to_idx']
    first_key = name_to_idx.keys()[0]
    # FIXME: str(column_name) is hack
    if isinstance(first_key, (unicode, str)):
        column_names = map(str, column_names)
    return [name_to_idx[column_name] for column_name in column_names]

def extract_view_column_info(M_c, X_L, view_idx):
    view_state_i = X_L['view_state'][view_idx]
    column_names = view_state_i['column_names']
    # view_state_i ordering should match global ordering
    column_component_suffstats = view_state_i['column_component_suffstats']
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
    
def create_component_model(column_metadata, column_hypers, suffstats):
    suffstats = copy.deepcopy(suffstats)
    count = suffstats.pop('N')
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
    cluster_component_models = dict()
    for global_column_idx in zipped_column_info:
        column_metadata, column_hypers, column_component_suffstats = \
            zipped_column_info[global_column_idx]
        cluster_component_suffstats = column_component_suffstats[cluster_idx]
        component_model = create_component_model(
            column_metadata, column_hypers, cluster_component_suffstats)
        cluster_component_models[global_column_idx] = component_model
    return cluster_component_models

def create_empty_cluster_model(zipped_column_info):
    cluster_component_models = dict()
    for global_column_idx in zipped_column_info:
        column_metadata, column_hypers, column_component_suffstats = \
            zipped_column_info[global_column_idx]
        component_model = create_component_model(column_metadata,
                                                 column_hypers, dict(N=None))
        cluster_component_models[global_column_idx] = component_model
    return cluster_component_models

def create_cluster_models(M_c, X_L, view_idx, which_columns=None):
    zipped_column_info, row_partition_model = extract_view_column_info(
        M_c, X_L, view_idx)
    if which_columns is not None:
        zipped_column_info = get_column_info_subset(
            zipped_column_info, which_columns)
    num_clusters = len(row_partition_model['counts'])
    cluster_models = []
    for cluster_idx in range(num_clusters):
        cluster_model = create_cluster_model(
            zipped_column_info, row_partition_model, cluster_idx
            )
        cluster_models.append(cluster_model)
    empty_cluster_model = create_empty_cluster_model(zipped_column_info)
    cluster_models.append(empty_cluster_model)
    return cluster_models

def determine_cluster_data_logp(cluster_model, cluster_sampling_constraints,
                                X_D_i, cluster_idx):
    logp = 0
    for column_idx, column_constraint_dict \
            in cluster_sampling_constraints.iteritems():
        if column_idx in cluster_model:
            other_constraint_values = []
            for other_row, other_value in column_constraint_dict['others']:
                if X_D_i[other_row]==cluster_idx:
                    other_constraint_values.append(other_value)
            this_constraint_value = column_constraint_dict['this']
            component_model = cluster_model[column_idx]
            logp += component_model.calc_element_predictive_logp_constrained(
                this_constraint_value, other_constraint_values)
    return logp

def get_cluster_sampling_constraints(Y, query_row):
    constraint_dict = dict()
    if Y is not None:
        for constraint in Y:
            constraint_row, constraint_col, constraint_value = constraint
            is_same_row = constraint_row == query_row
            if is_same_row:
                constraint_dict[constraint_col] = dict(this=constraint_value)
                constraint_dict[constraint_col]['others'] = []
        for constraint in Y:
            constraint_row, constraint_col, constraint_value = constraint
            is_same_row = constraint_row == query_row
            is_same_col = constraint_col in constraint_dict
            if is_same_col and not is_same_row:
                other = (constraint_row, constraint_value)
                constraint_dict[constraint_col]['others'].append(other)
    return constraint_dict

def get_draw_constraints(X_L, X_D, Y, draw_row, draw_column):
    constraint_values = []
    if Y is not None:
        column_partition_assignments = X_L['column_partition']['assignments']
        view_idx = column_partition_assignments[draw_column]
        X_D_i = X_D[view_idx]
        try:
            draw_cluster = X_D_i[draw_row]
        except IndexError, e:
            draw_cluster = None
        for constraint in Y:
            constraint_row, constraint_col, constraint_value = constraint
            try:
                constraint_cluster = X_D_i[constraint_row]
            except IndexError, e:
                constraint_cluster = None
            if (constraint_col == draw_column) \
                    and (constraint_cluster == draw_cluster):
                constraint_values.append(constraint_value)
    return constraint_values

def determine_cluster_data_logps(M_c, X_L, X_D, Y, query_row, view_idx):
    logps = []
    cluster_sampling_constraints = \
        get_cluster_sampling_constraints(Y, query_row)
    relevant_constraint_columns = cluster_sampling_constraints.keys()
    cluster_models = create_cluster_models(M_c, X_L, view_idx,
                                           relevant_constraint_columns)
    X_D_i = X_D[view_idx]
    for cluster_idx, cluster_model in enumerate(cluster_models):
        logp = determine_cluster_data_logp(
            cluster_model, cluster_sampling_constraints, X_D_i, cluster_idx)
        logps.append(logp)
    return logps

def determine_cluster_crp_logps(view_state_i):
    counts = view_state_i['row_partition_model']['counts']
    # FIXME: remove branch after Avinash is done with old saved states 
    alpha = view_state_i['row_partition_model']['hypers'].get('alpha')
    if alpha is None:
        alpha = numpy.exp(view_state_i['row_partition_model']['hypers']['log_alpha'])
    counts_appended = numpy.append(counts, alpha)
    sum_counts_appended = sum(counts_appended)
    logps = numpy.log(counts_appended / float(sum_counts_appended))
    return logps

def determine_cluster_logps(M_c, X_L, X_D, Y, query_row, view_idx):
    view_state_i = X_L['view_state'][view_idx]
    cluster_crp_logps = determine_cluster_crp_logps(view_state_i)
    cluster_crp_logps = numpy.array(cluster_crp_logps)
    cluster_data_logps = determine_cluster_data_logps(M_c, X_L, X_D, Y,
                                                      query_row, view_idx)
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

def simple_predictive_sample_unobserved(M_c, X_L, X_D, Y, query_row,
                                        query_columns, get_next_seed, n=1):
    num_views = len(X_D)
    #
    cluster_logps_list = []
    # for each view
    for view_idx in range(num_views):
        # get the logp of the cluster of query_row in this view
        cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, query_row,
                                                view_idx)
        cluster_logps_list.append(cluster_logps)
    #
    samples_list = []
    for sample_idx in range(n):
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
        for query_column in query_columns:
            column_to_view[query_column] = get_which_view(query_column)
        view_to_cluster_model = dict()
        for which_view in list(set(column_to_view.values())):
            which_cluster = view_cluster_draws[which_view]
            cluster_model = create_cluster_model_from_X_L(M_c, X_L,
                                                          which_view,
                                                          which_cluster)
            view_to_cluster_model[which_view] = cluster_model
        #
        this_sample_draws = []
        for query_column in query_columns:
            which_view = get_which_view(query_column)
            cluster_model = view_to_cluster_model[which_view]
            component_model = cluster_model[query_column]
            draw_constraints = get_draw_constraints(X_L, X_D, Y,
                                                    query_row, query_column)
            SEED = get_next_seed()
            draw = component_model.get_draw_constrained(SEED,
                                                        draw_constraints)
            this_sample_draws.append(draw)
        samples_list.append(this_sample_draws)
    return samples_list


def multinomial_imputation_confidence(samples, imputed, column_hypers_i):
    max_count = sum(numpy.array(samples) == imputed)
    confidence = float(max_count) / len(samples)
    return confidence

def get_continuous_mass_within_delta(samples, center, delta):
    num_samples = len(samples)
    num_within_delta = sum(numpy.abs(samples - center) < delta)
    mass_fraction = float(num_within_delta) / num_samples
    return mass_fraction

def continuous_imputation_confidence(samples, imputed,
                                     column_component_suffstats_i):
    col_std = get_column_std(column_component_suffstats_i)
    delta = .1 * col_std
    confidence = get_continuous_mass_within_delta(samples, imputed, delta)
    return confidence

def continuous_imputation(samples, get_next_seed):
    imputed = numpy.median(samples)
    return imputed

def multinomial_imputation(samples, get_next_seed):
    counter = Counter(samples)
    max_tuple = counter.most_common(1)[0]
    max_count = max_tuple[1]
    counter_counter = Counter(counter.values())
    num_max_count = counter_counter[max_count]
    imputed = max_tuple[0]
    if num_max_count >= 1:
        # if there is a tie, draw randomly
        max_tuples = counter.most_common(num_max_count)
        values = [max_tuple[0] for max_tuple in max_tuples]
        random_state = numpy.random.RandomState(get_next_seed())
        draw = random_state.randint(len(values))
        imputed = values[draw]
    return imputed

# FIXME: ensure callers aren't passing continuous, multinomial
modeltype_to_imputation_function = {
    'normal_inverse_gamma': continuous_imputation,
    'symmetric_dirichlet_discrete': multinomial_imputation,
    }

modeltype_to_imputation_confidence_function = {
    'normal_inverse_gamma': continuous_imputation_confidence,
    'symmetric_dirichlet_discrete': multinomial_imputation_confidence,
    }

def impute(M_c, X_L, X_D, Y, Q, n, get_next_seed, return_samples=False):
    # FIXME: allow more than one cell to be imputed
    assert(len(Q)==1)
    #
    col_idx = Q[0][1]
    modeltype = M_c['column_metadata'][col_idx]['modeltype']
    assert(modeltype in modeltype_to_imputation_function)
    if get_is_multistate(X_L, X_D):
        samples = simple_predictive_sample_multistate(M_c, X_L, X_D, Y, Q,
                                           get_next_seed, n)
    else:
        samples = simple_predictive_sample(M_c, X_L, X_D, Y, Q,
                                           get_next_seed, n)
    samples = numpy.array(samples).T[0]
    imputation_function = modeltype_to_imputation_function[modeltype]
    e = imputation_function(samples, get_next_seed)
    if return_samples:
        return e, samples
    else:
        return e

def get_confidence_interval(imputed, samples, confidence=.5):
    deltas = numpy.array(samples) - imputed
    sorted_abs_delta = numpy.sort(numpy.abs(deltas))
    n_samples = len(samples)
    lower_index = int(numpy.floor(confidence * n_samples))
    lower_value = sorted_abs_delta[lower_index]
    upper_value = sorted_abs_delta[lower_index + 1]
    interval = numpy.mean([lower_value, upper_value])
    return interval

def get_column_std(column_component_suffstats_i):
    N = sum(map(gu.get_getname('N'), column_component_suffstats_i))
    sum_x = sum(map(gu.get_getname('sum_x'), column_component_suffstats_i))
    sum_x_squared = sum(map(gu.get_getname('sum_x_squared'), column_component_suffstats_i))
    #
    exp_x = sum_x / float(N)
    exp_x_squared = sum_x_squared / float(N)
    col_var = exp_x_squared - (exp_x ** 2)
    col_std = col_var ** .5
    return col_std

def get_column_component_suffstats_i(M_c, X_L, col_idx):
    column_name = M_c['idx_to_name'][str(col_idx)]
    view_idx = X_L['column_partition']['assignments'][col_idx]
    view_state_i = X_L['view_state'][view_idx]
    local_col_idx = view_state_i['column_names'].index(column_name)
    column_component_suffstats_i = \
        view_state_i['column_component_suffstats'][local_col_idx]
    return column_component_suffstats_i

def impute_and_confidence(M_c, X_L, X_D, Y, Q, n, get_next_seed):
    # FIXME: allow more than one cell to be imputed
    assert(len(Q)==1)
    col_idx = Q[0][1]
    modeltype = M_c['column_metadata'][col_idx]['modeltype']
    imputation_confidence_function = \
        modeltype_to_imputation_confidence_function[modeltype]
    #
    imputed, samples = impute(M_c, X_L, X_D, Y, Q, n, get_next_seed,
                        return_samples=True)
    if get_is_multistate(X_L, X_D):
        X_L = X_L[0]
        X_D = X_D[0]
    column_component_suffstats_i = \
        get_column_component_suffstats_i(M_c, X_L, col_idx)
    imputation_confidence = \
        imputation_confidence_function(samples, imputed,
                                       column_component_suffstats_i)
    return imputed, imputation_confidence

def determine_replicating_samples_params(X_L, X_D):
    view_assignments_array = X_L['column_partition']['assignments']
    view_assignments_array = numpy.array(view_assignments_array)
    views_replicating_samples = []
    for view_idx, view_zs in enumerate(X_D):
        is_this_view = view_assignments_array == view_idx
        this_view_columns = numpy.nonzero(is_this_view)[0]
        this_view_replicating_samples = []
        for cluster_idx, cluster_count in Counter(view_zs).iteritems():
            view_zs_array = numpy.array(view_zs)
            first_row_idx = numpy.nonzero(view_zs_array==cluster_idx)[0][0]
            Y = None
            Q = [
                (int(first_row_idx), int(this_view_column))
                for this_view_column in this_view_columns
                ]
            n = cluster_count
            replicating_sample = dict(
                Y=Y,
                Q=Q,
                n=n,
                )
            this_view_replicating_samples.append(replicating_sample)
        views_replicating_samples.append(this_view_replicating_samples)
    return views_replicating_samples

def get_is_multistate(X_L, X_D):
    if isinstance(X_L, (list, tuple)):
        assert isinstance(X_D, (list, tuple))
        assert len(X_L) == len(X_D)
        return True
    else:
        return False


# def determine_cluster_view_logps(M_c, X_L, X_D, Y):
#     get_which_view = lambda which_column: \
#         X_L['column_partition']['assignments'][which_column]
#     column_to_view = dict()
#     for which_column in which_columns:
#         column_to_view[which_column] = get_which_view(which_column)
#     num_views = len(X_D)
#     cluster_logps_list = []
#     for view_idx in range(num_views):
#         cluster_logps = determine_cluster_logps(M_c, X_L, X_D, Y, view_idx)
#         cluster_logps_list.append(cluster_logp)
#     return cluster_view_logps
