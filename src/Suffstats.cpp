#include "Suffstats.h"

using namespace std;

template <>
Suffstats<double>::Suffstats() {
  init_suff_hash();
}

template <>
Suffstats<double>::Suffstats(double r, double nu, double s, double mu) {
  init_suff_hash(r, nu, s, mu);
}

double get(const map<string, double> m, string key) {
  map<string, double>::const_iterator it = m.find(key);
  if(it == m.end()) return -1;
  return it->second;
}

template <class T>
void Suffstats<T>::get_suffstats(int &count_out, double &r, double &nu,
				 double &s, double &mu) const {
  count_out = count;
  r = get(suff_hash, "r");
  nu = get(suff_hash, "nu");
  s = get(suff_hash, "s");
  mu = get(suff_hash, "mu");
}

template<>
double Suffstats<double>::calc_logp() const {
  int count;
  double r, nu, s, mu;
  get_suffstats(count, r, nu, s, mu);
  return numerics::calc_continuous_logp(count, r, nu, s, continuous_log_Z_0);
}
  
template<>
double Suffstats<double>::calc_data_logp(double el) const {
  int count;
  double r, nu, s, mu;
  get_suffstats(count, r, nu, s, mu);
  return numerics::calc_continuous_suffstats_data_logp(count, r, nu, s, mu, el,
						       score);
}

template <>
double Suffstats<double>::insert_el(double el) {
  double score_0 = score;
  numerics::insert_to_continuous_suffstats(count,
					   suff_hash["r"], suff_hash["nu"],
					   suff_hash["s"], suff_hash["mu"],
					   el);
  score = calc_logp();
  double delta_score = score - score_0;
  return delta_score;
}

template<>
double Suffstats<double>::remove_el(double el) {
  double score_0 = score;
  numerics::remove_from_continuous_suffstats(count,
					     suff_hash["r"], suff_hash["nu"],
					     suff_hash["s"], suff_hash["mu"],
					     el);
  score = calc_logp();
  double delta_score = score - score_0;
  return delta_score;
}

template <>
void Suffstats<double>::init_suff_hash(double r, double nu, double s, double mu) {
  continuous_log_Z_0 = numerics::calc_continuous_logp(0, r, nu, s, 0);
  count = 0;
  suff_hash["r"] = r;
  suff_hash["nu"] = nu;
  suff_hash["s"] = s;
  suff_hash["mu"] = mu;
  score = 0;
}

void print_defaults() {
  cout << endl << "Default values" << endl;
  cout << "r0_0: " << r0_0 << endl;
  cout << "nu0_0: " << nu0_0 << endl;
  cout << "s0_0: " << s0_0 << endl;
  cout << "mu0_0: " << mu0_0 << endl;
  cout << "continuous_log_Z_0: " << numerics::calc_continuous_logp(0, r0_0, nu0_0, s0_0, 0) << endl;
}
