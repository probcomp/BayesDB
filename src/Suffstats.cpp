#include "Suffstats.h"

using namespace std;

// forward declare
double get(const map<string, double> m, string key);
template<>
double Suffstats<double>::calc_logp() const;

template <>
Suffstats<double>::Suffstats(double r, double nu, double s, double mu) {
  continuous_log_Z_0 = numerics::calc_continuous_logp(0, r, nu, s, 0);
  count = 0;
  score = 0;
  init_suff_hash();
  init_hyper_hash(r, nu, s, mu);
}

template <>
void Suffstats<double>::get_suffstats(int &count_out, double &sum_x, double &sum_x_sq) const {
  count_out = count;
  sum_x = get(suff_hash, "sum_x");
  sum_x_sq = get(suff_hash, "sum_x_sq");
}

template <>
void Suffstats<double>::get_hypers(double &r, double &nu, double &s, double &mu)  const {
  r = get(hyper_hash, "r");
  nu = get(hyper_hash, "nu");
  s = get(hyper_hash, "s");
  mu = get(hyper_hash, "mu");
}

template <>
double Suffstats<double>::insert_el(double el) {
  double score_0 = score;
  numerics::insert_to_continuous_suffstats(count, suff_hash["sum_x"],
					   suff_hash["sum_x_sq"], el);
  score = calc_logp();
  double delta_score = score - score_0;
  return delta_score;
}

template<>
double Suffstats<double>::remove_el(double el) {
  double score_0 = score;
  numerics::remove_from_continuous_suffstats(count, suff_hash["sum_x"],
					   suff_hash["sum_x_sq"], el);
  score = calc_logp();
  double delta_score = score - score_0;
  return delta_score;
}

template<>
double Suffstats<double>::set_hyper(string which_hyper, double value) {
  double score_0 = score;
  hyper_hash[which_hyper] = value;
  score = calc_logp();
  double score_delta = score - score_0;
  return score_delta;
}

template<>
double Suffstats<double>::calc_logp() const {
  int count;
  double sum_x, sum_x_sq;
  double r, nu, s, mu;
  get_suffstats(count, sum_x, sum_x_sq);
  get_hypers(r, nu, s, mu);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  return numerics::calc_continuous_logp(count, r, nu, s, continuous_log_Z_0);
}
  
template<>
double Suffstats<double>::calc_data_logp(double el) const {
  int count;
  double sum_x, sum_x_sq;
  double r, nu, s, mu;
  get_suffstats(count, sum_x, sum_x_sq);
  get_hypers(r, nu, s, mu);
  //
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_sq, el);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  double logp_prime = numerics::calc_continuous_logp(count, r, nu, s, continuous_log_Z_0);
  return logp_prime - score;
}

template<>
vector<double> Suffstats<double>::calc_hyper_conditional(string which_hyper, vector<double> grid) const {
  int count;
  double sum_x, sum_x_sq;
  double r, nu, s, mu;
  get_suffstats(count, sum_x, sum_x_sq);
  get_hypers(r, nu, s, mu);
  
  if(which_hyper=="r") {
    return numerics::calc_continuous_r_conditionals(grid, count, sum_x,
						    sum_x_sq, nu, s, mu);
  } else if(which_hyper=="nu"){
    return numerics::calc_continuous_nu_conditionals(grid, count, sum_x,
  						     sum_x_sq, r, s, mu);
  } else if(which_hyper=="s"){
    return numerics::calc_continuous_s_conditionals(grid, count, sum_x,
						    sum_x_sq, r, nu, mu);
  } else if(which_hyper=="mu"){
    return numerics::calc_continuous_mu_conditionals(grid, count, sum_x,
  						     sum_x_sq, r, nu, s);
  } else {
    // error condition
  }
}

template <>
void Suffstats<double>::init_suff_hash() {
  suff_hash["count"] = 0;
  suff_hash["sum_x"] = 0;
  suff_hash["sum_x_sq"] = 0;
}

template <>
void Suffstats<double>::init_hyper_hash(double r, double nu, double s, double mu) {
  hyper_hash["r"] = r;
  hyper_hash["nu"] = nu;
  hyper_hash["s"] = s;
  hyper_hash["mu"] = mu;
}

void print_defaults() {
  cout << endl << "Default values" << endl;
  cout << "r0_0: " << r0_0 << endl;
  cout << "nu0_0: " << nu0_0 << endl;
  cout << "s0_0: " << s0_0 << endl;
  cout << "mu0_0: " << mu0_0 << endl;
  cout << "continuous_log_Z_0: " << numerics::calc_continuous_logp(0, r0_0, nu0_0, s0_0, 0) << endl;
}

double get(const map<string, double> m, string key) {
  map<string, double>::const_iterator it = m.find(key);
  if(it == m.end()) return -1;
  return it->second;
}
