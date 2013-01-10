#include "ContinuousComponentModel.h"

using namespace std;

ContinuousComponentModel::ContinuousComponentModel(double r, double nu, double s, double mu) {
  count = 0;
  score = 0;
  init_hypers();
  init_suffstats();
  set_log_Z_0();
}

ContinuousComponentModel::ContinuousComponentModel() {
  ContinuousComponentModel(r0_0, nu0_0, s0_0, mu0_0);
}

double ContinuousComponentModel::calc_marginal_logp() const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_sq;
  get_hypers(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_sq);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  return numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
}

double ContinuousComponentModel::calc_predictive_logp(double element) const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_sq;
  get_hypers(r, nu, s, mu);
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
  get_hypers(r, nu, s, mu);
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
  }
}

double ContinuousComponentModel::insert(double element) {
  double score_0 = score;
  numerics::insert_to_continuous_suffstats(count,
					   suffstats["sum_x"],
					   suffstats["sum_x_sq"],
					   element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::remove(double element) {
  double score_0 = score;
  numerics::remove_from_continuous_suffstats(count,
					     suffstats["sum_x"],
					     suffstats["sum_x_sq"],
					     element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::set_hyper(string which_hyper, double value) {
  double score_0 = score;
  hypers[which_hyper] = value;
  set_log_Z_0();
  score = calc_marginal_logp();
  double score_delta = score - score_0;
  return score_delta;
}

void ContinuousComponentModel::set_log_Z_0() {
  double r, nu, s, mu;
  get_hypers(r, nu, s, mu);
  log_Z_0 = numerics::calc_continuous_logp(0, r, nu, s, 0);
}

void ContinuousComponentModel::init_hypers(double r, double nu, double s, double mu) {
  hypers["r"] = r;
  hypers["nu"] = nu;
  hypers["s"] = s;
  hypers["mu"] = mu;
}

void ContinuousComponentModel::init_hypers() {
  init_hypers(r0_0, nu0_0, s0_0, mu0_0);
}

void ContinuousComponentModel::init_suffstats() {
  suffstats["sum_x"] = 0;
  suffstats["sum_x_sq"] = 0;
}

void ContinuousComponentModel::get_suffstats(int &count_out, double &sum_x, double &sum_x_sq) const {
  count_out = count;
  sum_x = get(suffstats, "sum_x");
  sum_x_sq = get(suffstats, "sum_x_sq");
}

void ContinuousComponentModel::get_hypers(double &r, double &nu, double &s, double &mu)  const {
  r = get(hypers, "r");
  nu = get(hypers, "nu");
  s = get(hypers, "s");
  mu = get(hypers, "mu");
}

void print_defaults() {
  cout << endl << "Default values" << endl;
  cout << "r0_0: " << r0_0 << endl;
  cout << "nu0_0: " << nu0_0 << endl;
  cout << "s0_0: " << s0_0 << endl;
  cout << "mu0_0: " << mu0_0 << endl;
  cout << "log_Z_0: " << numerics::calc_continuous_logp(0, r0_0, nu0_0, s0_0, 0) << endl;
}
