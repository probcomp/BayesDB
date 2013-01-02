#include "Suffstats.h"

// is this confusing to require knowledge that
// log_Z_0 is logp(suffstats_0, count=0)
double continuous_log_Z_0 = numerics::calc_continuous_logp(0, r0, nu0, s0, 0);

double get(const std::map<std::string, double> m, std::string key) {
  std::map<std::string, double>::const_iterator it = m.find(key);
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
  return numerics::calc_continuous_logp(count, r, nu, s, 0);
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
void Suffstats<double>::init_suff_hash() {
  count = 0;
  suff_hash["nu"] = nu0;
  suff_hash["s"] = s0;
  suff_hash["r"] = r0;
  suff_hash["mu"] = mu0;
  score = 0;
}

void print_defaults() {
  std::cout << std::endl << "Default values" << std::endl;
  std::cout << "continuous_log_Z_0: " << continuous_log_Z_0 << std::endl;
  std::cout << "r0: " << r0 << std::endl;
  std::cout << "nu0: " << nu0 << std::endl;
  std::cout << "s0: " << s0 << std::endl;
  std::cout << "mu0: " << mu0 << std::endl;
  std::cout << std::endl;
}
