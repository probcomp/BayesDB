from collections import Counter

modeltypes = set(["asymmetric_beta_bernoulli", "normal_inverse_gamma", "pitmanyor_atom", "symmetric_dirichlet_discrete", "poisson_gamma"])])

def assert_map_consistency(map_1, map_2):
    assert(len(map_1)==len(map_2))
    for key in map_1:
        assert(key == map_2[map_1[key]])

def assert_mc_consistency(mc):
    assert_map_consistency(mc["name_to_idx"], mc["idx_to_name"])
    assert(len(mc["name_to_idx"])==len(mc["column_metadata"]))
    for column_metadata_i in column_metadata:
        assert(column_metadata_i["modeltype"] in modeltypes)
        assert_map_consistency(column_metadata_i["value_to_code"],
                               column_metadata_i["code_to_value"])

def assert_mr_consistency(mr):
    assert_map_consistency(mr["name_to_idx"], mr["idx_to_name"])

