#include "utils.h"
//
#include <fstream>      // fstream
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>

using namespace std;
using namespace boost;
using namespace boost::numeric::ublas;

std::ostream& operator<<(std::ostream& os, const std::map<int, double>& int_double_map) {
  std::map<int, double>::const_iterator it = int_double_map.begin();
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

std::string int_to_str(int i) {  
  std::stringstream out;
  out << i;
  std::string s = out.str();
  return s;
}


// FROM runModel_v2.cpp
/////////////////////////////////////////////////////////////////////
// expect a csv file of data
void LoadData(std::string file, boost::numeric::ublas::matrix<double>& M) {
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
