#include "utils.h"
//
#include <fstream>      // fstream
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <numeric>

using namespace std;
using namespace boost;
using namespace boost::numeric::ublas;

// FROM runModel_v2.cpp
/////////////////////////////////////////////////////////////////////
// expect a csv file of data
void LoadData(string file, boost::numeric::ublas::matrix<double>& M) {
  ifstream in(file.c_str());
  if (!in.is_open()) return;
  typedef tokenizer< char_separator<char> > Tokenizer;
  char_separator<char> sep(",");

  string line;
  int nrows = 0; 
  int ncols = 0;
  std::vector<string> vec;

  // get the size first
  while (std::getline(in,line)) {
    Tokenizer tok(line, sep);
    vec.assign(tok.begin(), tok.end());
    ncols = vec.end() - vec.begin();
    nrows++;
  }
  cout << "num rows = "<< nrows << "  num cols = " << ncols << endl;

  // create a matrix to hold data
  matrix<double> Data(nrows, ncols);
  
  // make second pass 
  in.clear();
  in.seekg(0);
  int r = 0;
  while (std::getline(in,line)) {
    Tokenizer tok(line, sep);
    vec.assign(tok.begin(), tok.end());
    int i = 0;
    for(i=0; i < vec.size() ; i++) {
      Data(r, i) = ::strtod(vec[i].c_str(), 0);
    }
    r++;
  }
  M = Data;
}

bool is_almost(double val1, double val2, double precision) {
  return abs(val1-val2) < precision;
}

// http://stackoverflow.com/a/11747023/1769715
std::vector<double> linspace(double a, double b, int n) {
  std::vector<double> values;
  double step = (b-a) / (n-1);
  while(a <= b) {
    values.push_back(a);
    a += step;
  }
  return values;
}

std::vector<double> log_linspace(double a, double b, int n) {
  std::vector<double> values = linspace(log(a), log(b), n);
  std::transform(values.begin(), values.end(), values.begin(), (double (*)(double))exp);
  return values;
}

std::vector<double> std_vector_sum(std::vector<double> vec1, std::vector<double> vec2) {
  assert(vec1.size()==vec2.size());
  std::vector<double> sum_vec;
  for(int i=0; i<vec1.size(); i++) {
    sum_vec.push_back(vec1[i] + vec2[i]);
  }
  return sum_vec;
}

std::vector<double> std_vector_sum(std::vector<std::vector<double> > vec_vec) {
  std::vector<double> sum_vec = vec_vec[0];
  std::vector<std::vector<double> >::iterator it = vec_vec.begin();
  it++;
  for(; it!=vec_vec.end(); it++) {
    sum_vec = std_vector_sum(sum_vec, *it);
  }
  return sum_vec;
}

double calc_sum_sq_deviation(std::vector<double> values) {
  double sum = std::accumulate(values.begin(), values.end(), 0.0);
  double mean = sum / values.size();
  double sum_sq_deviation = 0;
  for(std::vector<double>::iterator it = values.begin(); it!=values.end(); it++) {
    sum_sq_deviation += pow((*it) - mean, 2) ;
  }
  return sum_sq_deviation;
}

std::vector<double> extract_row(boost::numeric::ublas::matrix<double> data, int row_idx) {
  std::vector<double> row;
  for(int j=0;j < data.size2(); j++) {
    row.push_back(data(row_idx, j));
  }
  return row;
}

std::vector<double> extract_col(boost::numeric::ublas::matrix<double> data, int col_idx) {
  std::vector<double> col;
  for(int j=0;j < data.size1(); j++) {
    col.push_back(data(j, col_idx));
  }
  return col;
}

std::vector<double> append(std::vector<double> vec1, std::vector<double> vec2) {
  vec1.insert(vec1.end(), vec2.begin(), vec2.end());
  return vec1;
}  

std::vector<int> extract_global_ordering(std::map<int, int> global_to_local) {
  std::vector<int> global_indices(global_to_local.size(), -1);
  map<int,int>::iterator it;
  for(it=global_to_local.begin(); it!=global_to_local.end(); it++) {
    int global_idx = it->first;
    int local_idx = it->second;
    global_indices[local_idx] = global_idx;
  }
  return global_indices;
}

map<int, int> construct_lookup_map(std::vector<int> values) {
  map<int, int> lookup;
  for(int idx=0; idx<values.size(); idx++) {
    lookup[values[idx]] = idx;
  }
  return lookup;
}

map<int, int> remove_and_reorder(map<int, int> old_global_to_local,
				      int global_to_remove) {
  // extract current ordering
  std::vector<int> global_indices = extract_global_ordering(old_global_to_local);
  // remove
  int local_to_remove = old_global_to_local[global_to_remove];
  global_indices.erase(global_indices.begin() + local_to_remove);
  // constrcut and return
  return construct_lookup_map(global_indices);
}

std::vector<int> get_indices_to_reorder(std::vector<int> data_global_column_indices, std::map<int, int> global_to_local) {
  int num_local_cols = global_to_local.size();
  int num_data_cols = data_global_column_indices.size();
  std::vector<int> reorder_indices(num_local_cols, -1);
  for(int data_column_idx=0; data_column_idx<num_data_cols; data_column_idx++) {
    int global_column_idx = data_global_column_indices[data_column_idx];
    if(global_to_local.find(global_column_idx) != global_to_local.end()) {
      int local_idx = global_to_local[data_column_idx];
      reorder_indices[local_idx] = data_column_idx;
    }
  }
  return reorder_indices;  
}		   

std::vector<double> reorder_per_indices(std::vector<double> raw_values,
					std::vector<int> reorder_indices) {
  std::vector<double> arranged_values;
  std::vector<int>::iterator it;
  for(it=reorder_indices.begin(); it!=reorder_indices.end(); it++) {
    int raw_value_idx = *it;
    double raw_value = raw_values[raw_value_idx];
    arranged_values.push_back(raw_value);
  }
  return arranged_values;
}

std::vector<double> reorder_per_map(std::vector<double> raw_values,
				    std::vector<int> global_column_indices,
				    std::map<int, int> global_to_local) {
  std::vector<int> reorder_indices = get_indices_to_reorder(global_column_indices, global_to_local);
  return reorder_per_indices(raw_values, reorder_indices);
}

std::vector<std::vector<double> > reorder_per_map(std::vector<std::vector<double> > raw_values,
				    std::vector<int> global_column_indices,
				    std::map<int, int> global_to_local) {
  std::vector<int> reorder_indices = get_indices_to_reorder(global_column_indices, global_to_local);
  std::vector<std::vector<double> > arranged_values_v;
  std::vector<std::vector<double> >::iterator it;
  for(it=raw_values.begin(); it!=raw_values.end(); it++) {
    std::vector<double> arranged_values = reorder_per_indices(*it, reorder_indices);
							      
    arranged_values_v.push_back(arranged_values);
  }
  return arranged_values_v;
}
  
std::vector<int> create_sequence(int len, int start) {
  std::vector<int> sequence(len, 1);
  sequence[0] = start;
  std::partial_sum(sequence.begin(), sequence.end(), sequence.begin());
  return sequence;
}
