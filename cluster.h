#ifndef GUARD_cluster_h
#define GUARD_cluster_h

// #include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <set>
#include <stdio.h>
#include "assert.h"
//
#include "utils.h"
#include "suffstats.h"

template <class T> class cluster;
template <typename T> std::ostream& operator<<(std::ostream& os, const cluster<T>& cT);

template <class T>
class cluster {
 public:
  cluster<T>(int NUM_COLS): num_cols(NUM_COLS) { init_suffstats(); };
  void insert_row(std::vector<T> vT, int row_idx);
  void remove_row(std::vector<T> vT, int row_idx);
  std::map<int, double> calc_logps();
  double calc_sum_logp();
  double get_vector_logp(std::vector<T> vT);
  // for copying info out
  std::map<int, suffstats<T> >& get_suffstats_m();
  std::set<int>& get_global_row_indices();
  std::set<int>& get_global_col_indices();
  friend std::ostream& operator<< <>(std::ostream& os, const cluster<T>& cT);
 private:
  int num_cols;
  void init_suffstats();
  std::map<int, suffstats<T> > suffstats_m;
  std::set<int> global_row_indices;
  std::set<int> global_col_indices;
};

template <class T>
std::map<int, double> cluster<T>::calc_logps() {
  std::map<int, double> ret_map;
  typename std::map<int, suffstats<T> >::iterator it = suffstats_m.begin();
  for(; it!=suffstats_m.end(); it++) {
    double logp = it->second.calc_logp();
    ret_map[it->first] = logp;
  }
  return ret_map;
}


template <class T>
double cluster<T>::calc_sum_logp() {
  double sum_logp = 0;
  std::map<int, double> logp_map = calc_logps();
  typename std::map<int, double>::iterator it = logp_map.begin();
  for(; it!=logp_map.end(); it++) {
    sum_logp += it->second;
  }
  return sum_logp;
}

template <class T>
std::map<int, suffstats<T> >& cluster<T>::get_suffstats_m() {
  return suffstats_m;
}

template <class T>
std::set<int>& cluster<T>::get_global_row_indices() {
  return global_row_indices;
}

template <class T>
std::set<int>& cluster<T>::get_global_col_indices() {
  return global_col_indices;
}

template <typename T>
std::ostream& operator<<(std::ostream& os, const cluster<T>& cT) {
  typename std::map<int, suffstats<T> >::const_iterator it = cT.suffstats_m.begin();
  for(; it!= cT.suffstats_m.end(); it++) {
    os << it->first << " :: " <<  cT.global_row_indices << " :: " << it->second;
  }
  return os;
}

#endif // GUARD_cluster_h
