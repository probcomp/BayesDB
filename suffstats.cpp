#include "suffstats.h"

double log_Z_0 = static_calc_log_Z(r0, nu0, s0);

double static_calc_log_Z(double r, double nu, double s) {
  double nu_over_2 = .5 * nu;
  return nu_over_2 * (LOG_2 - log(s))			\
    + HALF_LOG_2PI					\
    - .5 * log(r)					\
    + lgamma(nu_over_2);
}

template<>
double suffstats<double>::calc_log_Z() {
  return static_calc_log_Z(suff_hash["r"], suff_hash["nu"], suff_hash["s"]);
}

template<>
double suffstats<double>::calc_logp() {
  return -count * HALF_LOG_2PI + calc_log_Z() - log_Z_0;
}

/*
  r' = r + n
  nu' = nu + n
  m' = m + (X-nm)/(r+n)
  s' = s + C + rm**2 - r'm'**2
*/
template <>
void suffstats<double>::insert_el(double el) {
  count += 1;
  //
  double nu_prime = suff_hash["nu"] + 1;
  double r_prime = suff_hash["r"] + 1;
  double mu_prime = suff_hash["mu"] + (el - suff_hash["mu"]) / r_prime;
  double s_prime = suff_hash["s"] + pow(el, 2)		\
    + (suff_hash["r"] * pow(suff_hash["mu"], 2))	\
    - r_prime * pow(mu_prime, 2);
  //
  suff_hash["nu"] = nu_prime;
  suff_hash["r"] = r_prime;
  suff_hash["mu"] = mu_prime;
  suff_hash["s"] = s_prime;
}

template<>
void suffstats<double>::remove_el(double el) {
  count -= 1;
  //
  double nu_prime = suff_hash["nu"] - 1;
  double r_prime = suff_hash["r"] - 1;
  double mu_prime = (suff_hash["r"] * suff_hash["mu"] - el) / r_prime;
  double s_prime = suff_hash["s"] - pow(el, 2)		\
    + (suff_hash["r"] * pow(suff_hash["mu"], 2))	\
    - r_prime * pow(mu_prime, 2);
  //
  suff_hash["nu"] = nu_prime;
  suff_hash["r"] = r_prime;
  suff_hash["mu"] = mu_prime;
  suff_hash["s"] = s_prime;
}

template <>
void suffstats<double>::init_suff_hash() {
  count = 0;
  suff_hash["nu"] = nu0;
  suff_hash["s"] = s0;
  suff_hash["r"] = r0;
  suff_hash["mu"] = mu0;
}

void print_defaults() {
  std::cout << std::endl << "Default values" << std::endl;
  std::cout << "log_Z_0: " << log_Z_0 << std::endl;
  std::cout << "nu0: " << nu0 << std::endl;
  std::cout << "s0: " << s0 << std::endl;
  std::cout << "r0: " << r0 << std::endl;
  std::cout << "mu0: " << mu0 << std::endl;
  std::cout << std::endl;
}
