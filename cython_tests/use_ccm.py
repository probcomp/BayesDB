import continuous_component_model_test as ccmt
import boost_matrix_test as bmt

hyper_map = dict()
hyper_map["mu"] = 1.0
hyper_map["s"] = 1.0
hyper_map["nu"] = 1.0
hyper_map["r"] = 1.0

ccmt.set_string_double_map(hyper_map)
component_model = ccmt.p_ContinuousComponentModel(hyper_map)
print component_model.calc_marginal_logp()
component_model.insert_element(1.0)
print component_model.calc_marginal_logp()
component_model.remove_element(1.0)
print component_model.calc_marginal_logp()

p_matrix = bmt.p_matrix(5,5)
print p_matrix
print "p_matrix.get(0, 0):", p_matrix.get(0, 0)
p_matrix.set(0,0, -1.)
print "p_matrix.get(0, 0):", p_matrix.get(0, 0)

