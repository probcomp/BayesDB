#ifndef GUARD_utils_h
#define GUARD_utils_h

#include <iostream>
#include <string>
#include <set>
#include <map>
#include <boost/numeric/ublas/matrix.hpp>

void LoadData(std::string file, boost::numeric::ublas::matrix<double>& M);

template <class K, class V>
std::ostream& operator<<(std::ostream& os, const std::map<K, V> in_map) {
  os << "{";
  typename std::map<K, V>::const_iterator it = in_map.begin();
  if(it != in_map.end()) {
    os << it->first << ":" << it->second;
    it++;
  }
  for(; it!=in_map.end(); it++) {
    os << ", " << it->first << " : " << it->second;
  }
  os << "}";
  return os;
}

template <class T>
std::ostream& operator<<(std::ostream& os, const std::set<T> sT) {
  os << "{";
  typename std::set<T>::const_iterator it = sT.begin();
  if(it != sT.end()) {
    os << *it;
    it++;
  }
  for(; it!=sT.end(); it++) {
    os << ", " << *it;
  }
  os << "}";
  return os;
}

template <class T>
std::ostream& operator<<(std::ostream& os, const std::vector<T> vT) {
  os << "{";
  typename std::vector<T>::const_iterator it = vT.begin();
  if(it != vT.end()) {
    os << *it;
    it++;
  }
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

template <class K, class V>
V get(const std::map<K, V> m, K key) {
  typename std::map<K, V>::const_iterator it = m.find(key);
  if(it == m.end()) return -1;
  return it->second;
}

std::vector<int> extract_global_ordering(std::map<int, int> global_to_local);
std::map<int, int> construct_lookup_map(std::vector<int> values);
std::map<int, int> remove_and_reorder(std::map<int, int> global_to_local,
				      int global_to_remove);

std::vector<int> get_indices_to_reorder(std::vector<int> data_global_column_indices, std::map<int, int> global_to_local);
std::vector<double> reorder_per_indices(std::vector<double> raw_values,
					std::vector<int> reorder_indices);
std::vector<double> reorder_per_map(std::vector<double> raw_values,
				    std::vector<int> global_column_indices,
				    std::map<int, int> global_to_local);
std::vector<std::vector<double> > reorder_per_map(std::vector<std::vector<double> > raw_values,
				    std::vector<int> global_column_indices,
				    std::map<int, int> global_to_local);

#endif // GUARD_utils_H
