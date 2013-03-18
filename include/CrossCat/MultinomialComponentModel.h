#ifndef GUARD_multinomialcomponentmodel_h
#define GUARD_multinomialcomponentmodel_h

#include "ComponentModel.h"
#include "numerics.h"
#include "utils.h"

class MultinomialComponentModel : public ComponentModel {
 public:
  MultinomialComponentModel(std::map<std::string, double> &in_hypers);
  MultinomialComponentModel(std::map<std::string, double> &in_hypers,
			    int count, std::map<std::string, double> counts);
  //
  // getters
  std::map<std::string, double> get_hypers() const;
  void get_hyper_values(int &K, double &dirichlet_alpha) const;
  void get_suffstats(int &count_out, std::map<std::string, double> &counts) const;
  double get_draw(int random_seed) const;
  //
  // calculators
  double calc_marginal_logp() const;
  double calc_element_predictive_logp(double element) const;
  double calc_element_predictive_logp_constrained(double element, std::vector<double> constraints) const;
  std::vector<double> calc_hyper_conditionals(std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  //
  // mutators
  double insert_element(double element);
  double remove_element(double element);
  double incorporate_hyper_update();
 protected:
  void set_log_Z_0();
  void init_suffstats();
 private:
};

#endif // GUARD_multinomialcomponentmodel_h
