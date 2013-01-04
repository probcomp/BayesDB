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

const static double r0 = 1.0;
const static double nu0 = 2.0;
const static double s0 = 2.0;
const static double mu0 = 0.0;
extern double continuous_log_Z_0;

template <class T> class Suffstats;
template <typename T> std::ostream& operator<<(std::ostream& os,
					       const Suffstats<T>& sT);

// the sufficient statistics of a single cluster for a single feature
template <class T>
class Suffstats {
 public:
  Suffstats<T>();
  Suffstats<T>(double r, double nu, double s, double mu);
  double insert_el(T el);
  double remove_el(T el);
  double get_score() const;
  int get_count() const;
  double calc_data_logp(T el) const;
  void get_suffstats(int &count, double &r, double &nu, double &s, double &mu
		     ) const;
  friend std::ostream& operator<< <>(std::ostream& os, const Suffstats<T>& sT);
  // calc_logp() should be a recalculation of what's cached in get_score
  double calc_logp() const;
 private:
  double score;
  int count;
  std::map<std::string, double> suff_hash;
  //
  void init_suff_hash(double r=r0, double nu=nu0, double s=s0, double mu=mu0);
};

template <>
void Suffstats<double>::init_suff_hash(double r, double nu, double s, double mu);

void print_defaults();

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
  os << std::endl;
}

template <class T>
double Suffstats<T>::get_score() const {
  return score;
}

template <class T>
int Suffstats<T>::get_count() const {
  return count;
}

#endif // GUARD_suffstats_h
