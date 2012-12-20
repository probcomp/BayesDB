#ifndef GUARD_suffstats_h
#define GUARD_suffstats_h

#define _USE_CMATH_DEFINES
#include <cmath>
#include <iostream>
#include <initializer_list>
#include <string>
#include <vector>
#include <map>


const static double LOG_2PI = log(2.0 * M_PI);
const static double HALF_LOG_2PI = .5 * LOG_2PI;
const static double LOG_2 = log(2.0);
const static double nu0 = 2.0;
const static double s0 = 2.0;
const static double r0 = 1.0;
const static double mu0 = 0.0;
extern double log_Z_0;

template <class T> class suffstats;
template <typename T> std::ostream& operator<<(std::ostream& os, const suffstats<T>& sT);

// the sufficient statistics of a single cluster for a single feature
template <class T>
class suffstats {
 public:
  suffstats<T>() { init_suff_hash();};
  void insert_el(T el);
  void remove_el(T el);
  double calc_logp() const;
  friend std::ostream& operator<< <>(std::ostream& os, const suffstats<T>& sT);
 private:
  int count;
  std::map<std::string, double> suff_hash;
  //
  void init_suff_hash();
  double calc_log_Z() const;
};

double static_calc_log_Z(double r, double nu, double s);
void print_defaults();

template <typename T>
std::ostream& operator<<(std::ostream& os, const suffstats<T>& sT) {
  os << "count: " << sT.count << std::endl;
  //
  std::map<std::string, double>::const_iterator it = sT.suff_hash.begin();
  os << it->first << ":" << it->second;
  it++;
  for(; it != sT.suff_hash.end(); it++) {
    os << ";\t" << it->first << ":" << it->second;
  }
  os << std::endl;
  os << "logp: " << sT.calc_logp() << std::endl;
}

#endif // GUARD_suffstats_h
