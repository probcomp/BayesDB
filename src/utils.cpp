#include "utils.h"
//
#include <fstream>      // fstream
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>

using namespace std;
using namespace boost;
using namespace boost::numeric::ublas;

std::ostream& operator<<(std::ostream& os, const map<int, double>& int_double_map) {
  map<int, double>::const_iterator it = int_double_map.begin();
  os << "{";
  if(it==int_double_map.end()) {
    os << "}";
    return os;
  }
  os << it->first << ":" << it->second;
  it++;
  for(; it!=int_double_map.end(); it++) {
    os << ", " << it->first << ":" << it->second;
  }
  os << "}";
  return  os;
}

std::ostream& operator<<(std::ostream& os, const map<int, int>& int_int_map) {
  map<int, int>::const_iterator it = int_int_map.begin();
  os << "{";
  if(it==int_int_map.end()) {
    os << "}";
    return os;
  }
  os << it->first << ":" << it->second;
  it++;
  for(; it!=int_int_map.end(); it++) {
    os << ", " << it->first << ":" << it->second;
  }
  os << "}";
  return  os;
}

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
