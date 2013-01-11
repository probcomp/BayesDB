#ifndef GUARD_utils_h
#define GUARD_utils_h

#include <iostream>
#include <string>
#include <set>
#include <map>
#include <boost/numeric/ublas/matrix.hpp>

void LoadData(std::string file, boost::numeric::ublas::matrix<double>& M);

template <class K, class V>
std::ostream& operator<<(std::ostream& os, const std::map<K, V> in_map);

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

bool is_almost(double val1, double val2, double precision);

std::vector<double> linspace(double a, double b, int n);
std::vector<double> log_linspace(double a, double b, int n);

std::vector<double> std_vector_sum(std::vector<double> vec1, std::vector<double> vec2);
std::vector<double> std_vector_sum(std::vector<std::vector<double> > vec_vec);

double calc_sum_sq_deviation(std::vector<double> values);
std::vector<double> extract_row(boost::numeric::ublas::matrix<double> data, int row_idx);
std::vector<double> extract_col(boost::numeric::ublas::matrix<double> data, int col_idx);
std::vector<double> append(std::vector<double> vec1, std::vector<double> vec2);

double get(const std::map<std::string, double> m, std::string key);

template <class K, class V>
V get(const std::map<K, V> m, K key);

template <class K, class V>
std::ostream& operator<<(std::ostream& os, const std::map<K, V> in_map) {
  typename std::map<K, V>::const_iterator it;
  os << "{";
  if(in_map.begin()!=in_map.end()) {
    os << it->first << ":" << it->second;
  }
  for(it=in_map.begin(); it!=in_map.end(); it++) {
    os << ", " << it->first << " : " << it->second;
  }
  os << "}";
  return os;
}

template <class K, class V>
V get(const std::map<K, V> m, K key) {
  typename std::map<K, V>::const_iterator it = m.find(key);
  if(it == m.end()) return -1;
  return it->second;
}

#endif // GUARD_utils_H

