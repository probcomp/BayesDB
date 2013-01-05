#ifndef GUARD_suffstats_h
#define GUARD_suffstats_h

#define _USE_CMATH_DEFINES
#include <cmath>
#include <iostream>
#include <initializer_list>
#include <string>
#include <vector>
#include <map>
#include <iomanip> // std::setprecision

#include "numerics.h"

const static double r0_0 = 1.0;
const static double nu0_0 = 2.0;
const static double s0_0 = 2.0;
const static double mu0_0 = 0.0;

template <class T> class Suffstats;
template <typename T> std::ostream& operator<<(std::ostream& os,
					       const Suffstats<T>& sT);

// the sufficient statistics of a single cluster for a single feature
template <class T>
class Suffstats {
 public:
  Suffstats<T>();
  Suffstats<T>(double r, double nu, double s, double mu);
  //
  // getters
  int get_count() const;
  void get_suffstats(int &count, double &r, double &nu, double &s, double &mu
		     ) const;
  double get_score() const;
  //
  // mutators
  double insert_el(T el);
  double remove_el(T el);
  //
  // helpers
  double calc_logp() const;
  double calc_data_logp(T el) const;
  friend std::ostream& operator<< <>(std::ostream& os, const Suffstats<T>& sT);
 private:
  int count;
  std::map<std::string, double> suff_hash;
  double continuous_log_Z_0;
  double score;
  //
  void init_suff_hash(double r=r0_0, double nu=nu0_0, double s=s0_0, double mu=mu0_0);
};

// forward declare
template <>
void Suffstats<double>::init_suff_hash(double r, double nu, double s, double mu);

template <class T>
int Suffstats<T>::get_count() const {
  return count;
}

template <class T>
double Suffstats<T>::get_score() const {
  return score;
}

template <typename T>
std::ostream& operator<<(std::ostream& os, const Suffstats<T>& sT) {
  os << "count: " << sT.count << std::endl;
  //
  std::map<std::string, double>::const_iterator it = sT.suff_hash.begin();
  os << it->first << ":" << it->second;
  it++;
  for(; it != sT.suff_hash.end(); it++) {
    os << ";\t" << it->first << ":" << std::setprecision(3) << std::fixed << it->second;
  }
  os << ";\tscore:" << sT.get_score();
}

void print_defaults();

#endif // GUARD_suffstats_h
