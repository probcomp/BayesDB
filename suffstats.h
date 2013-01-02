#ifndef GUARD_suffstats_h
#define GUARD_suffstats_h

#define _USE_CMATH_DEFINES
#include <cmath>
#include <iostream>
#include <initializer_list>
#include <string>
#include <vector>
#include <map>

#include "numerics.h"

const static double nu0 = 2.0;
const static double s0 = 2.0;
const static double r0 = 1.0;
const static double mu0 = 0.0;
extern double continuous_log_Z_0;

template <class T> class suffstats;
template <typename T> std::ostream& operator<<(std::ostream& os,
					       const suffstats<T>& sT);

// the sufficient statistics of a single cluster for a single feature
template <class T>
class suffstats {
 public:
  suffstats<T>() { init_suff_hash();};
  double insert_el(T el);
  double remove_el(T el);
  // calc_logp() should be a recalculation of what's cached in get_score
  double calc_logp() const;
  double get_score() const;
  double calc_data_logp(T el) const;
  void get_suffstats(double &r, double &nu, double &s, double &mu,
		     double &count) const;
  friend std::ostream& operator<< <>(std::ostream& os, const suffstats<T>& sT);
 private:
  double score;
  int count;
  std::map<std::string, double> suff_hash;
  //
  void init_suff_hash();
};

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
  os << ";\tscore:" << sT.get_score();
  os << std::endl;
}

template <class T>
double suffstats<T>::get_score() const {
  return score;
}


#endif // GUARD_suffstats_h
