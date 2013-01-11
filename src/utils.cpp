#include "utils.h"
//
#include <fstream>      // fstream
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <numeric>

using namespace std;
using namespace boost;
using namespace boost::numeric::ublas;

string int_to_str(int i) {  
  std::stringstream out;
  out << i;
  string s = out.str();
  return s;
}


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

double get(const map<string, double> m, string key) {
  typename map<string, double>::const_iterator it = m.find(key);
  if(it == m.end()) return -1;
  return it->second;
}
