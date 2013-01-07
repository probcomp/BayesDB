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
#include "Suffstats.h"


template <class T> class Suffstats;
template <class T> class Cluster;
template <typename T> std::ostream& operator<<(std::ostream& os,
					       const Cluster<T>& cT);

template <class T>
class Cluster {
 public:
  Cluster<T>(): num_cols(5) { init_suffstats(); };
  Cluster<T>(int NUM_COLS): num_cols(NUM_COLS) { init_suffstats(); };
  //
  // getters
  int get_count() const;
  double get_score() const;
  Suffstats<T> get_suffstats_i(int idx) const;
  std::set<int> get_global_row_indices();
  std::set<int> get_global_col_indices();
  //
  // mutators
  double insert_row(std::vector<T> vT, int row_idx);
  double remove_row(std::vector<T> vT, int row_idx);
  double set_hyper(int which_col, std::string which_hyper, double value);
  //
  // calculators
  double calc_data_logp(std::vector<T> vT) const;
  std::map<int, double> calc_logps();
  double calc_sum_logp();
  std::vector<double> calc_hyper_conditional(int which_col, std::string which_hyper, std::vector<double> hyper_grid) const;
  //
  // helpers
  friend std::ostream& operator<< <>(std::ostream& os, const Cluster<T>& cT);
 private:
  double score;
  int num_cols;
  int count;
  void init_suffstats();
  std::map<int, Suffstats<T> > suffstats_m;
  std::set<int> global_row_indices;
  std::set<int> global_col_indices;
};

template <class T>
int Cluster<T>::get_count() const {
  return count;
}

template <class T>
double Cluster<T>::get_score() const {
  return score;
}

template <class T>
Suffstats<T> Cluster<T>::get_suffstats_i(int idx) const {
  typename std::map<int, Suffstats<T> >::const_iterator it = \
    suffstats_m.find(idx);
  if(it == suffstats_m.end()) {
    // FIXME : how to fail properly?
    assert(1==0);
    Suffstats<T> st;
    return st;
  }
  return it->second;
}

template <class T>
std::set<int> Cluster<T>::get_global_row_indices() {
  return global_row_indices;
}

template <class T>
std::set<int> Cluster<T>::get_global_col_indices() {
  return global_col_indices;
}

template <class T>
std::map<int, double> Cluster<T>::calc_logps() {
  std::map<int, double> ret_map;
  typename std::map<int, Suffstats<T> >::iterator it = suffstats_m.begin();
  for(; it!=suffstats_m.end(); it++) {
    double logp = it->second.calc_logp();
    ret_map[it->first] = logp;
  }
  return ret_map;
}

template <class T>
double Cluster<T>::calc_sum_logp() {
  double sum_logp = 0;
  std::map<int, double> logp_map = calc_logps();
  typename std::map<int, double>::iterator it = logp_map.begin();
  for(; it!=logp_map.end(); it++) {
    sum_logp += it->second;
  }
  return sum_logp;
}

template <typename T>
std::ostream& operator<<(std::ostream& os, const Cluster<T>& cT) {
  typename std::map<int, Suffstats<T> >::const_iterator it = cT.suffstats_m.begin();
  for(; it!= cT.suffstats_m.end(); it++) {
    os << "suffstats idx: " << it->first << " :: ";
    os <<  cT.global_row_indices << " :: " << it->second << std::endl;
  }
  os << "========" << std::endl;
  os <<"cluster score: " << cT.get_score() << std::endl;
  return os;
}

#endif // GUARD_cluster_h
