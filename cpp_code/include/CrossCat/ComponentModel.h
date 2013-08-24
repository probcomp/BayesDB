#ifndef GUARD_componentmodel_h
#define GUARD_componentmodel_h

#define _USE_CMATH_DEFINES
#include <cmath>
#include <iostream>
#include <sstream>
#include <map>
#include <string>
#include <vector>
#include "utils.h"
#include "constants.h"
#include <boost/random/student_t_distribution.hpp>
#include <boost/math/distributions/students_t.hpp>      
#include <boost/random/mersenne_twister.hpp>

class ComponentModel {
 public:
  //
  // getters
  std::map<std::string, double> get_hypers() const;
  int get_count() const;
  std::map<std::string, double> get_suffstats() const;
  std::map<std::string, double> _get_suffstats() const;
  //
  //
  // calculators
  virtual double calc_marginal_logp() const;
  virtual double calc_element_predictive_logp(double element) const;
  virtual double calc_element_predictive_logp_constrained(double element, std::vector<double> constraints) const;
  virtual std::vector<double> calc_hyper_conditionals(std::string which_hyper,
						      std::vector<double> hyper_grid) const;
  //
  // mutators
  virtual double insert_element(double element);
  virtual double remove_element(double element);
  virtual double incorporate_hyper_update();
  //
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const ComponentModel &cm);
  // make protected later
  std::map<std::string, double> *p_hypers;
  std::string to_string(std::string join_str="\n") const;
 protected:
  int count;
  double log_Z_0;
  double score;
  //
  // helpers
  virtual void set_log_Z_0();
  virtual void init_suffstats();
 private:
};

#endif // GUARD_componentmodel_h
