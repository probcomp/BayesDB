#include "suffstats.h"

double static_calc_log_Z(double r, double nu, double s) {
  double nu_over_2 = nu / 2.0;
  return nu_over_2 * log(2.0/s) + HALF_LOG_2PI - .5 * log(r) + lgamma(nu_over_2);
}

template<>
double suffstats<double>::calc_log_Z() {
  return static_calc_log_Z(suff_hash["r"], suff_hash["nu"], suff_hash["s"]);
}

template<>
double suffstats<double>::calc_logp() {
  return -(count / 2.0) * LOG_2PI + calc_log_Z() - suff_hash["log_Z_0"];
}

/*
  r' += n
  nu' += n
  m' += (X-nm)/(r+n)
  s' += C + rm**2 - r'm'**2
*/

template <>
void suffstats<double>::insert_el(double el) {
  count += 1;
  //
  double nu_prime = suff_hash["nu"] + 1;
  double r_prime = suff_hash["r"] + 1;
  double mu_prime = suff_hash["mu"] + (el - suff_hash["mu"]) / r_prime;
  double s_prime = suff_hash["s"] + pow(el, 2) +	\
    (suff_hash["r"] * pow(suff_hash["mu"], 2)) -	\
    r_prime * pow(mu_prime, 2);
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
  double s_prime = suff_hash["s"] - pow(el, 2) +	\
    (suff_hash["r"] * pow(suff_hash["mu"], 2)) -	\
    r_prime * pow(mu_prime, 2);
  //
  suff_hash["nu"] = nu_prime;
  suff_hash["r"] = r_prime;
  suff_hash["mu"] = mu_prime;
  suff_hash["s"] = s_prime;
}

template <>
void suffstats<double>::init_suff_hash() {
  count = 0;
  suff_hash["nu0"] = 2;
  suff_hash["s0"] = 2;
  suff_hash["r0"] = 1;
  suff_hash["mu0"] = 0;
  //
  suff_hash["nu"] = suff_hash["nu0"];
  suff_hash["s"] = suff_hash["s0"];
  suff_hash["r"] = suff_hash["r0"];
  suff_hash["mu"] = suff_hash["mu0"];
  //
  suff_hash["log_Z_0"] = calc_log_Z();
}

template <class T>
void suffstats<T>::print() {
  std::cout << "count: " << count << std::endl;
  //
  std::map<std::string, double>::iterator it = suff_hash.begin();
  std::cout << it->first << ":" << it->second;
  it++;
  for(; it != suff_hash.end(); it++) {
    std::cout << ";\t" << it->first << ":" << it->second;
  }
  std::cout << std::endl;
}

int main(int argc, char** argv) {
  std::cout << "Hello World!" << std::endl;
  
  suffstats<double> suffD;
  suffD.insert_el(1.0);
  suffD.print();
  suffD.insert_el(2.0);
  suffD.print();
  suffD.remove_el(2.0);
  suffD.print();
  //
  suffD.insert_el(2.0);
  suffD.print();
  suffD.insert_el(3.0);
  suffD.print();
  double logp = suffD.calc_logp();
  std::cout << "logp: " << logp << std::endl;
  // std::cout << "log_Z_0: " << suffD.suff_hash["log_Z_0"] << std::endl;

  std::cout << "Goodbye World!" << std::endl;
}
