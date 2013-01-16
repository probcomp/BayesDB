#ifndef GUARD_multinomialcomponentmodel_h
#define GUARD_multinomialcomponentmodel_h

#include "ComponentModel.h"
#include "numerics.h"
#include "utils.h"

class MultinomialComponentModel : public ComponentModel {
 public:
  MultinomialComponentModel(std::map<std::string, double> &in_hyper_hash);
  //
  // getters
  void get_hyper_values(int &K, double &dirichlet_alpha) const;
  void get_suffstats(std::map<std::string, int> counts) const;
  //
  // calculators
  double calc_marginal_logp() const;
  double calc_element_predictive_logp(std::string element) const;
  std::vector<double> calc_hyper_conditionals(std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  //
  // mutators
  double insert_element(string element) {}
  double remove_element(string element) {}
  double incorporate_hyper_update();
 protected:
  void set_log_Z_0();
  void init_suffstats();
 private:
};

#endif // GUARD_multinomialcomponentmodel_h
