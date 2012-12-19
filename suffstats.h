#ifndef GUARD_suffstats_h
#define GUARD_suffstats_h

#define _USE_CMATH_DEFINES
#include <cmath>
#include <iostream>
#include <initializer_list>
#include <string>
#include <vector>
#include <map>

/*
//http://www.gotw.ca/gotw/079.htm
struct _suffstats {
  typedef std::map<std::string, double> suff_hash;
};
//  typename _suffstats<T>::suff_hash suff_hash;
*/

const double LOG_2PI = log(2.0 * M_PI);
const double HALF_LOG_2PI = .5 * log(2.0 * M_PI);

// the sufficient statistics of a single cluster for a single feature
template <class T>
class suffstats {
 public:
  void init_suff_hash();
  suffstats<T>() { init_suff_hash();};
  void insert_el(T el);
  void remove_el(T el);
  double calc_logp();
  double calc_log_Z();
  void print();
  // _suffstats<T> get_suffstats();
 private:
  int count;
  std::map<std::string, double> suff_hash;
};

#endif // GUARD_suffstats_h
