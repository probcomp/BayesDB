from collections import Counter

modeltypes = set(["asymmetric_beta_bernoulli", "normal_inverse_gamma", "pitmanyor_atom", "symmetric_dirichlet_discrete", "poisson_gamma"])

def assert_map_consistency(map_1, map_2):
    assert(len(map_1)==len(map_2))
    for key in map_1:
        assert(key == map_2[map_1[key]])

def verify_keys(keys, in_dict):
    for key in keys:
        assert key in in_dict

def asymmetric_beta_bernoulli_hyper_validator(in_dict):
    required_keys = ["strength", "balance"]
    veify_keys(required_keys, in_dict)
    #
    assert 0 <= in_dict["balance"]
    assert in_dict["balance"] <= 1

def normal_inverse_gamma_hyper_validator(in_dict):
    required_keys = ["mu", "kappa", "alpha", "beta"]
    verify_keys(required_keys, in_dict)
    #
    assert 0 < in_dict["kappa"]
    assert 0 < in_dict["alpha"]
    assert 0 < in_dict["beta"]

def pitmanyor_atom_hyper_validator(in_dict):
    required_keys = ["gamma", "alpha"]
    verify_keys(required_keys, in_dict)
    #
    assert 0 < in_dict["gamma"]
    assert in_dict["gamma"] < 1
    assert -gamma < in_dict["alpha"]

def symmetric_dirichlet_discrete_hyper_validator(in_dict):
    required_keys = ["log_alpha", "K"]
    verify_keys(required_keys, in_dict)
    # FIXME: > 2? >0?
    assert in_dict["K"] > 1

def poisson_gamma_hyper_validator(in_dict):
    nrequired_keys = ["kappa", "beta"]
    verify_keys(required_keys, in_dict)
    #
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

def normal_inverse_gamma_suffstats_validator(in_dict):
    required_keys = ["sum_x", "sum_x_squared", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert 0 <= in_dict["sum_x_squared"]

def pitmanyor_atom_suffstats_validator(in_dict):
    required_keys = ["counts", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert sum(in_dict["counts"]) == in_dict["N"]

def symmetric_dirichlet_discrete_suffstats_validator(in_dict):
    required_keys = ["counts", "N"]
    verify_keys(required_keys, in_dict)
    #
    assert sum(in_dict["counts"]) == in_dict["N"]

def poisson_gamma_suffstats_validator(in_dict):
    # FIXME: required_keys = ["kappa", "beta", "N"]
    # FIXME: verify_keys(required_keys, in_dict)
    #
    pass

modeltype_suffstats_validators = {
    "asymmetric_beta_bernoulli": asymmetric_beta_bernoulli_suffstats_validator,
    "normal_inverse_gamma": normal_inverse_gamma_suffstats_validator,
    "pitmanyor_atom": pitmanyor_atom_suffstats_validator,
    "symmetric_dirichlet_discrete": symmetric_dirichlet_discrete_suffstats_validator,
    "poisson_gamma": poisson_gamma_suffstats_validator
}

def assert_mc_consistency(mc):
    assert_map_consistency(mc["name_to_idx"], mc["idx_to_name"])
    assert(len(mc["name_to_idx"])==len(mc["column_metadata"]))
    for column_metadata_i in mc["column_metadata"]:
        assert(column_metadata_i["modeltype"] in modeltypes)
        assert_map_consistency(column_metadata_i["value_to_code"],
                               column_metadata_i["code_to_value"])

def assert_mr_consistency(mr):
    assert_map_consistency(mr["name_to_idx"], mr["idx_to_name"])

def assert_xl_view_state_consistency(view_state_i, mc):
    column_names = view_state_i["columnNames"]
    for column_name, column_component_suffstats_i in \
            zip(column_names, view_state_i["columnComponentSuffstats"]):
        global_column_idx = mc["name_to_idx"][column_name]
        modeltype = mc["column_metadata"][global_column_idx]["modeltype"]
        suffstats_validator = modeltype_suffstats_validators[modeltype]
        for component_suffstats in column_component_suffstats_i:
            suffstats_validator(component_suffstats)

def assert_xl_consistency(xl, mc):
    assignment_counts = Counter(xl["assignments"])
    # sum(xl["counts"]) == len(assignments) is a byproduct of above
    for idx, count in enumerate(xl["counts"]):
        assert(count==assignment_counts[idx])
    for column_metadata_i, columnHypers_i in \
            zip(mc["column_metadata"], xl["columnHypers"]):
        modeltype = column_metadata_i["modeltype"]
        validator = modeltype_hyper_validators[modeltype]
        validator(columnHypers_i)
        if modeltype == "symmetric_dirichlet_discrete":
            # FIXME: can't do this, you may know there are N values but only have
            # M datapoints where M < N
            # assert columnHypers_i["K"] == len(column_metadata_i["value_to_code"])
            pass
    for view_state_i in xl["viewState"]:
        assert_xl_view_state_consistency(view_state_i)

def assert_xd_consistency(xd, mr, mc):
    assert xd.shape[0] == len(mr["name_to_idx"])
    assert xd.shape[1] == len(mc["name_to_idx"])

def assert_t_consistency(T, mr, mc):
    if T["orientation"] == "row_major":
        assert T["dimensions"][0] == T["data"].shape[0]
        assert T["dimensions"][1] == T["data"].shape[1]
        assert T["dimensions"][0] == len(mr["name_to_idx"])
        assert T["dimensions"][1] == len(mc["name_to_idx"])
    else:
        assert T["dimensions"][1] == T["data"].shape[0]
        assert T["dimensions"][0] == T["data"].shape[1]
        assert T["dimensions"][1] == len(mr["name_to_idx"])
        assert T["dimensions"][0] == len(mc["name_to_idx"])

if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str)
    args = parser.parse_args()
    filename = args.filename
    #
    with open(filename) as fh:
        one_line = "".join(fh.readlines()).translate(None,"\n\t ")
        print one_line
        parsed_sample = json.loads(one_line)
    M_c = parsed_sample["M_c"]
    M_r = parsed_sample["M_r"]
    assert_mc_consistency(M_c)
    assert_mr_consistency(M_r)
