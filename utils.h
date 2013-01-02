#ifndef GUARD_utils_h
#define GUARD_utils_h

#include <iostream>
#include <string>
#include <boost/numeric/ublas/matrix.hpp>
#include "Cluster.h"
#include "Suffstats.h"

void LoadData(std::string file, boost::numeric::ublas::matrix<double>& M);

std::ostream& operator<<(std::ostream& os, const std::map<int, double>& int_double_map);
std::ostream& operator<<(std::ostream& os, const std::map<int, int>& int_int_map);

std::string int_to_str(int i);

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
std::ostream& operator<<(std::ostream& os, const std::set<T> sT) {
  typename std::set<T>::const_iterator it = sT.begin();
  os << "{";
  if(it==sT.end()) {
    os << "}";
    return os;
  }
  os << *it;
  it++;
  for(; it!=sT.end(); it++) {
    os << ", " << *it;
  }
  os << "}";
  return os;
}

template <class T>
std::ostream& operator<<(std::ostream& os, const std::vector<T> vT) {
  typename std::vector<T>::const_iterator it = vT.begin();
  os << "{";
  if(it==vT.end()) {
    os << "}";
    return os;
  }
  os << *it;
  it++;
  for(; it!=vT.end(); it++) {
    os << ", " << *it;
  }
  os << "}";
  return os;
}

#endif // GUARD_utils_H
