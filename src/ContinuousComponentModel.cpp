#include "ContinuousComponentModel.h"

using namespace std;

ContinuousComponentModel::ContinuousComponentModel(map<string, double> &in_hypers) {
  count = 0;
  score = 0;
  p_hypers = &in_hypers;
  init_suffstats();
  set_log_Z_0();
}

double ContinuousComponentModel::calc_marginal_logp() const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_sq;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_sq);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  return numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
}

double ContinuousComponentModel::calc_element_predictive_logp(double element) const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_sq;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_sq);
  //
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_sq, element);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  double logp_prime = numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
  return logp_prime - score;
}

vector<double> ContinuousComponentModel::calc_hyper_conditionals(string which_hyper, vector<double> hyper_grid) const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_sq;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_sq);
  
  if(which_hyper=="r") {
    return numerics::calc_continuous_r_conditionals(hyper_grid, count, sum_x,
						    sum_x_sq, nu, s, mu);
  } else if(which_hyper=="nu"){
    return numerics::calc_continuous_nu_conditionals(hyper_grid, count, sum_x,
						     sum_x_sq, r, s, mu);
  } else if(which_hyper=="s"){
    return numerics::calc_continuous_s_conditionals(hyper_grid, count, sum_x,
						    sum_x_sq, r, nu, mu);
  } else if(which_hyper=="mu"){
    return numerics::calc_continuous_mu_conditionals(hyper_grid, count, sum_x,
						     sum_x_sq, r, nu, s);
  } else {
    // error condition
    vector<double> error;
    return error;
  }
}

double ContinuousComponentModel::insert_element(double element) {
  double score_0 = score;
  numerics::insert_to_continuous_suffstats(count,
					   suffstats["sum_x"],
					   suffstats["sum_x_sq"],
					   element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::remove_element(double element) {
  double score_0 = score;
  numerics::remove_from_continuous_suffstats(count,
					     suffstats["sum_x"],
					     suffstats["sum_x_sq"],
					     element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::incorporate_hyper_update() {
  double score_0 = score;
  // hypers[which_hyper] = value; // set by owner of hypers object
  set_log_Z_0();
  score = calc_marginal_logp();
  double score_delta = score - score_0;
  return score_delta;
}

void ContinuousComponentModel::set_log_Z_0() {
  double r, nu, s, mu;
  get_hyper_doubles(r, nu, s, mu);
  log_Z_0 = numerics::calc_continuous_logp(0, r, nu, s, 0);
}

void ContinuousComponentModel::init_suffstats() {
  suffstats["sum_x"] = 0;
  suffstats["sum_x_sq"] = 0;
}

void ContinuousComponentModel::get_suffstats(int &count_out, double &sum_x,
					     double &sum_x_sq) const {
  count_out = count;
  sum_x = get(suffstats, (string) "sum_x");
  sum_x_sq = get(suffstats, (string) "sum_x_sq");
}

map<string, double> ContinuousComponentModel::get_suffstats() const {
  return suffstats;
}

void ContinuousComponentModel::get_hyper_doubles(double &r, double &nu,
						 double &s, double &mu)  const {
  r = get(*p_hypers, (string) "r");
  nu = get(*p_hypers, (string) "nu");
  s = get(*p_hypers, (string) "s");
  mu = get(*p_hypers, (string) "mu");
}
