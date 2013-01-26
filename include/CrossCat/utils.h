#ifndef GUARD_utils_h
#define GUARD_utils_h

#include "numerics.h"
#include "RandomNumberGenerator.h"
//
#include <iostream>
#include <string>
#include <sstream> // stringstream in stringify()
#include <set>
#include <map>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>

typedef boost::numeric::ublas::matrix<double> MatrixD;

void LoadData(std::string file, MatrixD& M);

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
  os << "[";
  typename std::vector<T>::const_iterator it = vT.begin();
  if(it != vT.end()) {
    os << *it;
    it++;
  }
  for(; it!=vT.end(); it++) {
    os << ", " << *it;
  }
  os << "]";
  return os;
}

bool is_almost(double val1, double val2, double precision);

std::vector<double> linspace(double a, double b, int n);
std::vector<double> log_linspace(double a, double b, int n);
std::vector<int> create_sequence(int len, int start=0);

std::vector<double> std_vector_sum(std::vector<double> vec1,
				   std::vector<double> vec2);
std::vector<double> std_vector_sum(std::vector<std::vector<double> > vec_vec);

double calc_sum_sq_deviation(std::vector<double> values);
std::vector<double> extract_row(const MatrixD data, int row_idx);
std::vector<double> extract_col(const MatrixD data, int col_idx);
				
std::vector<double> append(std::vector<double> vec1, std::vector<double> vec2);

template <class K, class V>
bool in(const std::map<K, V> m, K key) {
  typename std::map<K, V>::const_iterator it = m.find(key);
  bool is_in = it != m.end();
  return is_in;
}

template <class K, class V>
V get(const std::map<K, V> m, K key) {
  typename std::map<K, V>::const_iterator it = m.find(key);
  if(it == m.end()) assert(1==0);
  return it->second;
}

std::vector<int> extract_global_ordering(std::map<int, int> global_to_local);
template <class T>
std::map<int, T> construct_lookup_map(std::vector<int> keys, std::vector<T> values);
std::map<int, std::vector<double> > construct_data_map(const MatrixD data);
std::map<int, int> construct_lookup_map(std::vector<int> values);
std::map<int, int> remove_and_reorder(std::map<int, int> global_to_local,
				      int global_to_remove);

std::vector<int> get_indices_to_reorder(std::vector<int> data_global_column_indices, std::map<int, int> global_to_local);
std::vector<double> reorder_per_indices(std::vector<double> raw_values,
					std::vector<int> reorder_indices);
std::vector<double> reorder_per_map(std::vector<double> raw_values,
				    std::vector<int> global_column_indices,
				    std::map<int, int> global_to_local);
std::vector<std::vector<double> > reorder_per_map(std::vector<std::vector<double> > raw_values, std::vector<int> global_column_indices, std::map<int, int> global_to_local);

std::vector<std::vector<int> > determine_crp_init(std::vector<int> global_row_indices,
						  double alpha,
						  RandomNumberGenerator &rng);

void copy_column(const MatrixD fromM, int from_col, MatrixD &toM, int to_col);
MatrixD extract_columns(const MatrixD fromM, std::vector<int> from_cols);

template <class T>
std::vector<T> set_to_vector(const std::set<T> in_set) {
  std::vector<T> out_vector;
  typename std::set<T>::const_iterator it;
  for(it=in_set.begin(); it!=in_set.end(); it++) {
    T element = *it;
    out_vector.push_back(element);
  }
  return out_vector;
}


template <class T>
std::map<T, int> set_to_map(const std::set<T> in_set) {
  std::map<T, int> out_map;
  typename std::set<T>::const_iterator it;
  for(it=in_set.begin(); it!=in_set.end(); it++) {
    T element = *it;
    int out_map_size = out_map.size();
    out_map[element] = out_map_size;
  }
  return out_map;
}

template <class T>
std::string stringify(T element) {
  std::stringstream ss;
  ss << element;
  return ss.str();
}

int intify(std::string str);

template <class K, class V>
std::map<V, std::set<K> > group_by_value(std::map<K, V> in_map) {
  std::map<V, std::set<K> > out_map;
  typename std::map<K, V>::iterator it;
  for(it=in_map.begin(); it!=in_map.end(); it++) {
    K k = it->first;
    V v = it->second;
    out_map[v].insert(k);
  }
  return out_map;
}

// semi numeric functions
std::vector<double> create_crp_alpha_grid(int n_values, int N_GRID);
void construct_continuous_base_hyper_grids(int n_grid,
					   std::vector<double> col_data,
					   std::vector<double> &r_grid,
					   std::vector<double> &nu_grid);
void construct_continuous_specific_hyper_grid(int n_grid,
					      std::vector<double> col_data,
					      std::vector<double> &s_grid,
					      std::vector<double> &mu_grid);

template <class T>
boost::numeric::ublas::matrix<T> vector_to_matrix(std::vector<T> vT) {
  boost::numeric::ublas::matrix<T> matrix_out(1, vT.size());
  for(int i=0; i<vT.size(); i++) {
    matrix_out(0, i) = vT[i];
  }
  return matrix_out;
}
				 
#endif // GUARD_utils_H
