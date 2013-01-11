#ifndef GUARD_continuouscomponentmodel_h
#define GUARD_continuouscomponentmodel_h

#include <iomanip> // std::setprecision
#include "ComponentModel.h"
#include "numerics.h"
#include "utils.h"

const static double r0_0 = 1.0;
const static double nu0_0 = 2.0;
const static double s0_0 = 2.0;
const static double mu0_0 = 0.0;

class ContinuousComponentModel : public ComponentModel {
 public:
  ContinuousComponentModel(double r, double nu, double s, double mu);
  ContinuousComponentModel();
  //
  // getters
  void get_hyper_doubles(double &r, double &nu, double &s, double &mu) const;
  void get_suffstats(int &count_out, double &sum_x, double &sum_x_sq) const;
  //
  // calculators
  double calc_marginal_logp() const;
  double calc_predictive_logp(double element) const;
  std::vector<double> calc_hyper_conditionals(std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  //
  // mutators
  double insert(double element);
  double remove(double element);
  double set_hyper(std::string which_hyper, double hyper_value);
 protected:
  void set_log_Z_0();
  void init_hypers();
  void init_suffstats();
 private:
  void init_hypers(double r, double nu, double s, double mu);
};

void print_defaults();

#endif // GUARD_continuouscomponentmodel_h

