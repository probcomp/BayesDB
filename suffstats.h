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

double static_calc_log_Z(double r, double nu, double s);
void print_defaults();

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
  std::cout << "logp: " << calc_logp() << std::endl;
}

#endif // GUARD_suffstats_h

/*
//http://www.gotw.ca/gotw/079.htm
struct _suffstats {
  typedef std::map<std::string, double> suff_hash;
};
//  typename _suffstats<T>::suff_hash suff_hash;
*/
