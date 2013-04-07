from collections import Counter
#
import tabular_predDB.python_utils.file_utils as fu


modeltypes = set(["asymmetric_beta_bernoulli", "normal_inverse_gamma", "pitmanyor_atom", "symmetric_dirichlet_discrete", "poisson_gamma"])

strify_dict = lambda in_dict: dict([
        (str(key), str(value))
        for key, value in in_dict.iteritems()
        ])

##################
# helpers for cython saved states
def strify_M_r(M_r):
    M_r['name_to_idx'] = strify_dict(M_r['name_to_idx'])
    M_r['idx_to_name'] = strify_dict(M_r['idx_to_name'])
    return M_r

def strify_M_c(M_c):
    M_c['name_to_idx'] = strify_dict(M_c['name_to_idx'])
    M_c['idx_to_name'] = strify_dict(M_c['idx_to_name'])
    for column_metadata_i in M_c['column_metadata']:
        column_metadata_i['value_to_code'] = \
            strify_dict(column_metadata_i['value_to_code'])
        column_metadata_i['code_to_value'] = \
            strify_dict(column_metadata_i['code_to_value'])
    return M_c

def dirichelt_alpha_to_alpha(in_dict):
    in_dict['alpha'] = in_dict.pop('dirichlet_alpha')
    return in_dict

def convert_column_hypers(in_dict):
    if 'r' in in_dict:
        in_dict['kappa'] = in_dict.pop('r')
        in_dict['alpha'] = in_dict.pop('nu')
        in_dict['beta'] = in_dict.pop('s')
    else:
        in_dict = dirichelt_alpha_to_alpha(in_dict)
    return in_dict

def convert_suffstats(view_state_i):
    column_component_suffstats = view_state_i['column_component_suffstats']
    for col_idx, col_suffstats in enumerate(column_component_suffstats):
        for cluster_idx, suffstats in enumerate(col_suffstats):
            if 'sum_x' not in suffstats:
                N = suffstats.pop('N')
                col_suffstats[cluster_idx] = dict(counts=suffstats, N=N)
    return view_state_i

def convert_X_L(X_L):
    for column_hypers in X_L['column_hypers']:
        column_hypers = convert_column_hypers(column_hypers)
    for view_state_i in X_L['view_state']:
        convert_suffstats(view_state_i)
    return X_L

def convert_T(T):
    num_rows = len(T)
    num_cols = len(T[0])
    dims = [num_rows, num_cols]
    T = dict(data=T, orientation="row_major", dimensions=dims)
    return T
# helpers for cython saved states
##################

def assert_map_consistency(map_1, map_2):
    assert(len(map_1)==len(map_2))
    for key in map_1:
        assert(key == map_2[map_1[key]])

def verify_keys(keys, in_dict):
    for key in keys:
        assert key in in_dict, "%s not in %s" % (key, in_dict)

def asymmetric_beta_bernoulli_hyper_validator(in_dict):
    required_keys = ["strength", "balance"]
    verify_keys(required_keys, in_dict)
    assert 0 <= in_dict["strength"]
    assert 0 <= in_dict["balance"]
    assert in_dict["balance"] <= 1

def normal_inverse_gamma_hyper_validator(in_dict):
    required_keys = ["mu", "kappa", "alpha", "beta"]
    verify_keys(required_keys, in_dict)
    #
    # mu ranges from negative infinity to positive infinity
    # kappa, alpha, beta range from 0 to infinity
    assert 0 < in_dict["kappa"]
    assert 0 <= in_dict["alpha"]
    assert 0 <= in_dict["beta"]

def pitmanyor_atom_hyper_validator(in_dict):
    required_keys = ["gamma", "alpha"]
    verify_keys(required_keys, in_dict)
    #
    assert 0 < in_dict["gamma"]
    assert in_dict["gamma"] < 1
    assert -gamma < in_dict["alpha"]

def symmetric_dirichlet_discrete_hyper_validator(in_dict):
    required_keys = ["alpha", "K"]
    verify_keys(required_keys, in_dict)
    # range of alpha is negative infinity to positive infinity
    assert 0 < in_dict["alpha"]
    assert 1 < in_dict["K"]

def poisson_gamma_hyper_validator(in_dict):
    nrequired_keys = ["kappa", "beta"]
    verify_keys(required_keys, in_dict)
    # kappa and beta range from (0, infinity)
    assert 0 < in_dict["kappa"]
    assert 0 < in_dict["beta"]

modeltype_hyper_validators = {
    "asymmetric_beta_bernoulli": asymmetric_beta_bernoulli_hyper_validator,
    "normal_inverse_gamma": normal_inverse_gamma_hyper_validator,
    "pitmanyor_atom": pitmanyor_atom_hyper_validator,
    "symmetric_dirichlet_discrete": symmetric_dirichlet_discrete_hyper_validator,
    "poisson_gamma": poisson_gamma_hyper_validator
}

def asymmetric_beta_bernoulli_suffstats_validator(in_dict):
    required_keys = ["0_count", "1_count", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert in_dict["0_count"] + in_dict["1_count"] == in_dict["N"]
    assert 0 <= in_dict["0_count"]
    assert 0 <= in_dict["1_count"]

def normal_inverse_gamma_suffstats_validator(in_dict):
    required_keys = ["sum_x", "sum_x_squared", "N"]
    verify_keys(required_keys, in_dict)
    assert 0 <= in_dict["sum_x_squared"]
    assert 0 <= in_dict["N"]

def pitmanyor_atom_suffstats_validator(in_dict):
    required_keys = ["counts", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert sum(in_dict["counts"]) == in_dict["N"]

def symmetric_dirichlet_discrete_suffstats_validator(in_dict):
    required_keys = ["counts", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert sum(in_dict["counts"].values()) == in_dict["N"]

def poisson_gamma_suffstats_validator(in_dict):
    required_keys = ["summed_values", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert 0 <= in_dict["summed_values"]
    assert 0 <= in_dict["N"]

modeltype_suffstats_validators = {
    "asymmetric_beta_bernoulli": asymmetric_beta_bernoulli_suffstats_validator,
    "normal_inverse_gamma": normal_inverse_gamma_suffstats_validator,
    "pitmanyor_atom": pitmanyor_atom_suffstats_validator,
    "symmetric_dirichlet_discrete": symmetric_dirichlet_discrete_suffstats_validator,
    "poisson_gamma": poisson_gamma_suffstats_validator
}

def assert_mc_consistency(mc):
    # check the name to index maps
    assert_map_consistency(mc["name_to_idx"], mc["idx_to_name"])
    # check that there is metadata for each column
    assert(len(mc["name_to_idx"])==len(mc["column_metadata"]))
    # check that each metadata includes a model type and code-value map
    for column_metadata_i in mc["column_metadata"]:
        assert(column_metadata_i["modeltype"] in modeltypes)
        assert_map_consistency(column_metadata_i["value_to_code"],
                               column_metadata_i["code_to_value"])

def assert_mr_consistency(mr):
    assert_map_consistency(mr["name_to_idx"], mr["idx_to_name"])

def assert_xl_view_state_consistency(view_state_i, mc):
    column_names = view_state_i["column_names"]
    column_component_suffstats = view_state_i["column_component_suffstats"]
    for column_name_i, column_component_suffstats_i in \
            zip(column_names, column_component_suffstats):
        # keys must be strings
        global_column_idx = mc["name_to_idx"][str(column_name_i)]
        modeltype = mc["column_metadata"][int(global_column_idx)]["modeltype"]
        suffstats_validator = modeltype_suffstats_validators[modeltype]
        for component_suffstats in column_component_suffstats_i:
            suffstats_validator(component_suffstats)

def assert_xl_consistency(xl, mc):
    assignment_counts = Counter(xl["column_partition"]["assignments"])
    # sum(xl["counts"]) == len(assignments) is a byproduct of above
    for idx, count in enumerate(xl["column_partition"]["counts"]):
        assert(count==assignment_counts[idx])
    for column_metadata_i, column_hypers_i in \
            zip(mc["column_metadata"], xl["column_hypers"]):
        modeltype = column_metadata_i["modeltype"]
        validator = modeltype_hyper_validators[modeltype]
        validator(column_hypers_i)
        if modeltype == "symmetric_dirichlet_discrete":
            num_codes_metadata = len(column_metadata_i["value_to_code"])
            num_codes_hypers = column_hypers_i["K"]
            assert num_codes_metadata == num_codes_hypers
            # FIXME: should assert len(suffstats['counts']) <= num_codes_hypers
    for view_state_i in xl["view_state"]:
        assert_xl_view_state_consistency(view_state_i, mc)
    assert sum(xl["column_partition"]["counts"]) == len(mc["name_to_idx"])

    
def assert_xd_consistency(xd, mr, mc):
    # is number of row labels in xd's first view equal to number of row names?
    assert len(xd[0]) == len(mr["name_to_idx"])
    # do all views have the same number of row labels?
    assert len(set(map(len, xd))) == 1

def assert_t_consistency(T, mr, mc):
    # is it rectangular?
    assert len(set(map(len, T["data"]))) == 1
    if T["orientation"] == "row_major":
        assert T["dimensions"][0] == len(T["data"])
        assert T["dimensions"][1] == len(T["data"][0])
        assert T["dimensions"][0] == len(mr["name_to_idx"])
        assert T["dimensions"][1] == len(mc["name_to_idx"])
    else: # "column_major"
        assert T["dimensions"][1] == len(T["data"])
        assert T["dimensions"][0] == len(T["data"][0])
        assert T["dimensions"][1] == len(mr["name_to_idx"])
        assert T["dimensions"][0] == len(mc["name_to_idx"])

def assert_other(mr, mc, xl, xd, T):
    # is the number of views in xd equal to their cached counts in xl?
    assert len(xl["column_partition"]["counts"]) == len(xd)

if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser('A script to validate a json file\'s compliance with the predictive-DB spec')
    parser.add_argument('filename', type=str)
    args = parser.parse_args()
    filename = args.filename
    #
    if filename.endswith('.pkl.gz'):
        parsed_sample = fu.unpickle(filename)
        parsed_sample['M_r'] = strify_M_r(parsed_sample['M_r'])
        parsed_sample['M_c'] = strify_M_c(parsed_sample['M_c'])
        parsed_sample['X_L'] = convert_X_L(parsed_sample['X_L'])
        parsed_sample['T'] = convert_T(parsed_sample['T'])
    else:
        with open(filename) as fh:
            one_line = "".join(fh.readlines()).translate(None,"\n\t ")
            parsed_sample = json.loads(one_line)

    M_c = parsed_sample["M_c"]
    M_r = parsed_sample["M_r"]
    X_L = parsed_sample["X_L"]
    X_D = parsed_sample["X_D"]
    T = parsed_sample["T"]

    assert_mc_consistency(M_c)
    assert_mr_consistency(M_r)
#assert_xl_view_state_consistency(view_state_i, mc)
    assert_xl_consistency(X_L, M_c)
    assert_xd_consistency(X_D, M_r, M_c)
    assert_t_consistency(T, M_r, M_c)
    assert_other(M_r, M_c, X_L, X_D, T)
