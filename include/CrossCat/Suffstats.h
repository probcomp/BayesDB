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
  Suffstats<T>(double r=r0_0, double nu=nu0_0, double s=s0_0, double mu=mu0_0);
  //
  // getters
  int get_count() const;
  void get_suffstats(int &count, double &sum_x, double &sum_x_sq) const;
  void get_hypers(double &r, double &nu, double &s, double &mu) const;
  std::map<std::string, double> get_hyper_hash() const;
  double get_score() const;
  //
  // mutators
  double insert_el(T el);
  double remove_el(T el);
  double set_hyper(std::string which_hyper, double value);
  //
  // helpers
  double calc_logp() const;
  double calc_data_logp(T el) const;
  std::vector<double> calc_hyper_conditional(std::string which_hyper, std::vector<double> hyper_grid) const;
  friend std::ostream& operator<< <>(std::ostream& os, const Suffstats<T>& sT);
 private:
  int count;
  std::map<std::string, double> suff_hash;
  std::map<std::string, double> hyper_hash;
  double continuous_log_Z_0;
  double score;
  //
  void set_log_Z_0();
  void init_suff_hash();
  void init_hyper_hash(double r=r0_0, double nu=nu0_0, double s=s0_0, double mu=mu0_0);
};

// forward declare
template <>
void Suffstats<double>::init_suff_hash();
template <>
void Suffstats<double>::init_hyper_hash(double r, double nu, double s, double mu);
template <>
void Suffstats<double>::set_log_Z_0();

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
  os << "suffstats: " << sT.suff_hash << std::endl;
  os << "hypers: " << sT.hyper_hash << std::endl;
  os << "score:" << sT.get_score();
}

void print_defaults();

#endif // GUARD_suffstats_h
