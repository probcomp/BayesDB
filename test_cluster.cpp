#include <iostream>
#include "cluster.h"
#include "utils.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

int main(int argc, char** argv) {
  std::cout << std::endl << "Hello World!" << std::endl;
  int i = 123;

  boost::numeric::ublas::matrix<double> Data;
  LoadData("SynData2.csv", Data);
  std::cout << Data << std::endl;

  cluster<double> cd(5); //hard code # columns
  std::cout << std::endl << "Init cluster" << std::endl;
  std::cout << cd << std::endl;


  for(i=0; i < 4; i++) {
    std::vector<double> V;
    for(int j=0;j < Data.size2(); j++) {
      V.push_back(Data(i,j));
    }
    cd.insert_row(V, i);
  }
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  //
  for(i=4; i < 8; i++) {
    std::vector<double> V;
    for(int j=0;j < Data.size2(); j++) {
      V.push_back(Data(i,j));
    }
    cd.insert_row(V, i);
  }
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  //
  print_defaults();

  std::map<int, double> logps = cd.calc_logps();
  std::cout << "logps: " << logps << std::endl;

  std::cout << std::endl << "Goodbye World!" << std::endl;
}
