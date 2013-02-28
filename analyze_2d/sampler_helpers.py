import numpy


def update_continuous_hypers(column_hypers, cluster_suffstats, cluster_count):
    r = column_hypers['r']
    nu = column_hypers['nu']
    mu = column_hypers['mu']
    s = column_hypers['s']
    sum_x = cluster_suffstats['sum_x']
    sum_x_sq = cluster_suffstats['sum_x_sq']
    #
    r_prime = r + cluster_count
    nu_prime = nu + cluster_count
    mu_prime = ((r * mu) + sum_x) / r_prime
    s_prime = s + sum_x_sq + (r * mu * mu) - (r_prime * mu_prime * mu_prime)
    #
    return r_prime, nu_prime, s_prime, mu_prime

def get_updated_continuous_hypers(p_State, view_idx, col_idx, cluster_idx):
    view_state_i = p_State.get_view_state()[view_idx]
    column_component_suffstats = view_state_i['column_component_suffstats'][col_idx]
    cluster_suffstats = column_component_suffstats[cluster_idx]
    column_hypers = p_State.get_column_hypers()[col_idx]
    cluster_count = view_state_i['row_partition_model']['counts'][cluster_idx]
    r, nu, s, mu = update_continuous_hypers(
        column_hypers, cluster_suffstats, cluster_count)
    return r, nu, s, mu

def generate_view_cluster_means(p_State, view_idx):
# def generate_view_cluster_hyper_posterior(p_State, view_idx):
    view_state_i = p_State.get_view_state()[view_idx]
    column_component_suffstats = view_state_i['column_component_suffstats']
    cluster_counts = view_state_i['row_partition_model']['counts']
    num_clusters = len(column_component_suffstats[0])
    column_idx_set = view_state_i['column_names']
    num_cols = len(column_idx_set)
    #
    cluster_posterior_hypers = []
    for cluster_idx in range(num_clusters):
        this_cluster_posterior_hypers = []
        for col_idx in sorted(list(column_idx_set)):
            r, nu, s, mu = get_updated_continuous_hypers(
                p_State, view_idx, col_idx, cluster_idx)
            this_cluster_posterior_hypers.append((r, nu, s, mu))
        cluster_posterior_hypers.append(this_cluster_posterior_hypers)
    return cluster_posterior_hypers

def generate_column_sample(random_state, p_State, view_idx, col_idx, cluster_idx):
    r, nu, s, mu = get_updated_continuous_hypers(p_State, view_idx, col_idx, cluster_idx)
    standard_t_draw = random_state.standard_t(nu)
    student_t_draw = standard_t_draw * (s * (r + 1)) / (nu * r) + mu
    return student_t_draw

def generate_cluster_draws(random_state, p_State, column_view_idx_lookup):
    view_state_list = p_State.get_view_state()
    num_cols = sum(map(lambda x: len(x['column_names']), view_state_list))
    view_cluster_draw = []
    for view_idx, view_state_i in enumerate(view_state_list):
        cluster_counts = view_state_i['row_partition_model']['counts']
        cluster_ps = numpy.array(cluster_counts) / float(sum(cluster_counts))
        which_cluster = random_state.multinomial(1, cluster_ps)
        which_cluster = numpy.nonzero(which_cluster)[0][0]
        view_cluster_draw.append(which_cluster)
    #
    column_cluster_draws = []
    for col_idx in range(num_cols):
        view_idx = column_view_idx_lookup[col_idx]
        which_cluster = view_cluster_draw[view_idx]
        column_cluster_draws.append(which_cluster)
    return column_cluster_draws

def generate_sample(random_state, p_State, column_view_idx_lookup):
    column_cluster_draws = generate_cluster_draws(random_state, p_State,
                                                  column_view_idx_lookup)
    print column_cluster_draws
    view_state_list = p_State.get_view_state()
    num_cols = sum(map(lambda x: len(x['column_names']), view_state_list))
    column_sample_values = []
    for col_idx in range(num_cols):
        which_view_idx = column_view_idx_lookup[col_idx]
        which_cluster_idx = column_cluster_draws[col_idx]
        column_sample_value = generate_column_sample(
            random_state, p_State, which_view_idx, col_idx, which_cluster_idx)
        column_sample_values.append(column_sample_value)
    return column_sample_values
