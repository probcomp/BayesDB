#ifndef GUARD_continuouscomponentmodel_h
#define GUARD_continuouscomponentmodel_h

#include "ComponentModel.h"
#include "numerics.h"
#include "utils.h"

class ContinuousComponentModel : public ComponentModel {
 public:
  ContinuousComponentModel(std::map<std::string, double> &in_hyper_hash);
  ContinuousComponentModel(std::map<std::string, double> &in_hyper_hash,
			   int COUNT, double SUM_X, double SUM_X_SQ);
  //
  // getters
  void get_hyper_doubles(double &r, double &nu, double &s, double &mu) const;
  void get_suffstats(int &count_out, double &sum_x, double &sum_x_sq) const;
  std::map<std::string, double> get_suffstats() const;
  double get_draw(int random_seed) const;
  double get_draw_constrained(int random_seed, std::vector<double> constraints) const;
  double get_predictive_cdf(double element, std::vector<double> constraints) const;
  double calc_element_predictive_cdf(double element) const;
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

#endif // GUARD_continuouscomponentmodel_h
