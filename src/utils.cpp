#include "utils.h"
//
#include <fstream>      // fstream
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <numeric>
#include <algorithm>

using namespace std;
using namespace boost;

using boost::numeric::ublas::project;
using boost::numeric::ublas::range;
using boost::numeric::ublas::matrix;

// FROM runModel_v2.cpp
/////////////////////////////////////////////////////////////////////
// expect a csv file of data
void LoadData(string file, matrix<double>& M) {
  ifstream in(file.c_str());
  if (!in.is_open()) return;
  typedef tokenizer< char_separator<char> > Tokenizer;
  char_separator<char> sep(",");

  string line;
  int nrows = 0; 
  int ncols = 0;
  vector<string> vec;

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
vector<double> linspace(double a, double b, int n) {
  vector<double> values;
  double step = (b-a) / (n-1);
  while(a <= b) {
    values.push_back(a);
    a += step;
  }
  return values;
}

vector<double> log_linspace(double a, double b, int n) {
  vector<double> values = linspace(log(a), log(b), n);
  std::transform(values.begin(), values.end(), values.begin(),
		 (double (*)(double))exp);
  return values;
}

vector<double> std_vector_sum(vector<double> vec1, vector<double> vec2) {
  assert(vec1.size()==vec2.size());
  vector<double> sum_vec;
  for(int i=0; i<vec1.size(); i++) {
    sum_vec.push_back(vec1[i] + vec2[i]);
  }
  return sum_vec;
}

vector<double> std_vector_sum(vector<vector<double> > vec_vec) {
  vector<double> sum_vec = vec_vec[0];
  vector<vector<double> >::iterator it = vec_vec.begin();
  it++;
  for(; it!=vec_vec.end(); it++) {
    sum_vec = std_vector_sum(sum_vec, *it);
  }
  return sum_vec;
}

double calc_sum_sq_deviation(vector<double> values) {
  double sum = std::accumulate(values.begin(), values.end(), 0.0);
  double mean = sum / values.size();
  double sum_sq_deviation = 0;
  for(vector<double>::iterator it = values.begin(); it!=values.end(); it++) {
    sum_sq_deviation += pow((*it) - mean, 2) ;
  }
  return sum_sq_deviation;
}

vector<double> extract_row(matrix<double> data, int row_idx) {
  vector<double> row;
  for(int j=0;j < data.size2(); j++) {
    row.push_back(data(row_idx, j));
  }
  return row;
}

vector<double> extract_col(matrix<double> data, int col_idx) {
  vector<double> col;
  for(int j=0;j < data.size1(); j++) {
    col.push_back(data(j, col_idx));
  }
  return col;
}

vector<double> append(vector<double> vec1, vector<double> vec2) {
  vec1.insert(vec1.end(), vec2.begin(), vec2.end());
  return vec1;
}  

vector<int> extract_global_ordering(map<int, int> global_to_local) {
  vector<int> global_indices(global_to_local.size(), -1);
  map<int,int>::iterator it;
  for(it=global_to_local.begin(); it!=global_to_local.end(); it++) {
    int global_idx = it->first;
    int local_idx = it->second;
    global_indices[local_idx] = global_idx;
  }
  return global_indices;
}

template <class T>
map<int, T> construct_lookup_map(vector<int> keys, vector<T> values) {
  assert(keys.size()==values.size());
  map<int, T> lookup;
  for(int idx=0; idx<keys.size(); idx++) {
    lookup[keys[idx]] = values[idx];
  }
  return lookup;
}

map<int, int> construct_lookup_map(vector<int> keys) {
  return construct_lookup_map(keys, create_sequence(keys.size()));
}

map<int, vector<double> > construct_data_map(MatrixD data) {
  int num_rows = data.size1();
  map<int, vector<double> > data_map;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    data_map[row_idx] = extract_row(data, row_idx);
  }
  return data_map;
}

map<int, int> remove_and_reorder(map<int, int> old_global_to_local,
				 int global_to_remove) {
  // extract current ordering
  vector<int> global_indices = extract_global_ordering(old_global_to_local);
  // remove
  int local_to_remove = old_global_to_local[global_to_remove];
  global_indices.erase(global_indices.begin() + local_to_remove);
  // constrcut and return
  return construct_lookup_map(global_indices);
}

vector<int> get_indices_to_reorder(vector<int> data_global_column_indices,
				   map<int, int> global_to_local) {
  int num_local_cols = global_to_local.size();
  int num_data_cols = data_global_column_indices.size();
  vector<int> reorder_indices(num_local_cols, -1);
  for(int data_column_idx=0; data_column_idx<num_data_cols; data_column_idx++) {
    int global_column_idx = data_global_column_indices[data_column_idx];
    if(global_to_local.find(global_column_idx) != global_to_local.end()) {
      int local_idx = global_to_local[data_column_idx];
      reorder_indices[local_idx] = data_column_idx;
    }
  }
  return reorder_indices;  
}		   

vector<double> reorder_per_indices(vector<double> raw_values,
				   vector<int> reorder_indices) {
  vector<double> arranged_values;
  vector<int>::iterator it;
  for(it=reorder_indices.begin(); it!=reorder_indices.end(); it++) {
    int raw_value_idx = *it;
    double raw_value = raw_values[raw_value_idx];
    arranged_values.push_back(raw_value);
  }
  return arranged_values;
}

vector<double> reorder_per_map(vector<double> raw_values,
			       vector<int> global_column_indices,
			       map<int, int> global_to_local) {
  vector<int> reorder_indices = \
    get_indices_to_reorder(global_column_indices, global_to_local);
  return reorder_per_indices(raw_values, reorder_indices);
}

vector<vector<double> > reorder_per_map(vector<vector<double> > raw_values,
					vector<int> global_column_indices,
					map<int, int> global_to_local) {
  vector<int> reorder_indices = get_indices_to_reorder(global_column_indices, global_to_local);
  vector<vector<double> > arranged_values_v;
  vector<vector<double> >::iterator it;
  for(it=raw_values.begin(); it!=raw_values.end(); it++) {
    vector<double> arranged_values = reorder_per_indices(*it, reorder_indices);
    arranged_values_v.push_back(arranged_values);
  }
  return arranged_values_v;
}
  
vector<int> create_sequence(int len, int start) {
  vector<int> sequence(len, 1);
  if(len==0) return sequence;
  sequence[0] = start;
  std::partial_sum(sequence.begin(), sequence.end(), sequence.begin());
  return sequence;
}

void insert_into_counts(int draw, vector<int> &counts) {
  assert(draw<=counts.size());
  if(draw==counts.size()) {
    counts.push_back(1);
  } else {
    counts[draw]++;
  }
}

vector<int> determine_crp_init_counts(int num_datum, double alpha,
				      RandomNumberGenerator &rng) {
  vector<int> counts;
  double rand_u;
  int draw;
  int sum_counts = 0;
  for(int draw_idx=0; draw_idx<num_datum; draw_idx++) {
    rand_u = rng.next();
    draw = numerics::crp_draw_sample(counts, sum_counts, alpha, rand_u);
    sum_counts++;
    insert_into_counts(draw, counts);
  }
  return counts;
}

vector<vector<int> > determine_crp_init(vector<int> global_row_indices,
					double alpha,
					RandomNumberGenerator &rng) {
  int num_datum = global_row_indices.size();
  vector<int> counts = determine_crp_init_counts(num_datum, alpha, rng);
  std::random_shuffle(global_row_indices.begin(), global_row_indices.end());
  vector<int>::iterator it = global_row_indices.begin();
  vector<vector<int> > cluster_indices_v;
  for(int cluster_idx=0; cluster_idx<counts.size(); cluster_idx++) {
    int count = counts[cluster_idx];
    vector<int> cluster_indices(count, -1);
    std::copy(it, it+count, cluster_indices.begin());
    cluster_indices_v.push_back(cluster_indices);
    it += count;
  }
  return cluster_indices_v;
}

void copy_column(MatrixD fromM, int from_col, MatrixD &toM, int to_col) {
  assert(fromM.size1()==toM.size1());
  int num_rows = fromM.size1();
  project(toM, range(0, num_rows), range(to_col, to_col+1)) = \
    project(fromM, range(0, num_rows), range(from_col, from_col+1));
}

MatrixD extract_columns(MatrixD fromM, vector<int> from_cols) {
  int num_rows = fromM.size1();
  int num_cols = from_cols.size();
  MatrixD toM(num_rows, num_cols);
  for(int to_col=0; to_col<num_cols; to_col++) {
    int from_col = from_cols[to_col];
    copy_column(fromM, from_col, toM, to_col);
  }
  return toM;
}
