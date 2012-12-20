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
#include "suffstats.h"

template <class T>
class cluster {
 public:
  cluster<T>(int NUM_COLS): num_cols(NUM_COLS) { init_suffstats(); };
  void insert_row(std::vector<T> vT, int row_idx);
  void remove_row(std::vector<T> vT, int col_idx);
  std::map<int, double> calc_logps();
  // for copying info out
  std::map<int, suffstats<T> >& get_suffstats_m();
  std::set<int>& get_global_row_indices();
  std::set<int>& get_global_col_indices();
  void print();
 private:
  int num_cols;
  void init_suffstats();
  std::map<int, suffstats<T> > suffstats_m;
  std::set<int> global_row_indices;
  std::set<int> global_col_indices;
};

template <class T>
std::map<int, double> cluster<T>::calc_logps() {
  // FIXME: UNIMPLEMENTED
  std::map<int, double> ret_map;
  return ret_map;
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

std::string int_to_str(int i) {  
  std::stringstream out;
  out << i;
  std::string s = out.str();
  return s;
}

template <class T>
std::string stringify_set(std::set<T> st) {
  typename std::set<T>::iterator it = st.begin();
  if(it==st.end()) return "{}";
  //
  std::string ret_string = "{";
  ret_string += int_to_str(*it);
  it++;
  for(; it!=st.end(); it++) {
    ret_string += ", " + int_to_str(*it);
  }
  ret_string += "}";
  return ret_string;
}

template <class T>
void cluster<T>::print() {
  typename std::map<int, suffstats<T> >::iterator it = \
    suffstats_m.begin();
  for(; it!= suffstats_m.end(); it++) {
    std::string indices_string = stringify_set(global_row_indices);
    std::cout << it->first << " :: " <<  indices_string << " :: ";
    it->second.print();
  }
}

#endif // GUARD_cluster_h
