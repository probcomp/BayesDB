import ContinuousComponentModel as CCM


hyper_map = dict()
hyper_map["mu"] = 1.0
hyper_map["s"] = 1.0
hyper_map["nu"] = 1.0
hyper_map["r"] = 2.0

CCM.set_string_double_map(hyper_map)
component_model = CCM.p_ContinuousComponentModel(hyper_map)
print component_model.calc_marginal_logp()
component_model.insert_element(2.3)
print component_model.calc_marginal_logp()
print "component_model.get_draw(0):", component_model.get_draw(0)
print "component_model.get_draw(1):", component_model.get_draw(1)
component_model.remove_element(2.3)
print component_model.calc_marginal_logp()
