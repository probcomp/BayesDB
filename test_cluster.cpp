#include <iostream>
#include "cluster.h"
#include "utils.h"
#include "numerics.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

int main(int argc, char** argv) {
  std::cout << std::endl << "Hello World!" << std::endl;
  int i = 123;
  double sum_sum_score_deltas;

  boost::numeric::ublas::matrix<double> Data;
  LoadData("SynData2.csv", Data);
  // std::cout << Data << std::endl;

  cluster<double> cd(5); //hard code # columns
  std::cout << std::endl << "Init cluster" << std::endl;
  std::cout << cd << std::endl;

  sum_sum_score_deltas = 0;
  for(i=0; i < 4; i++) {
    std::vector<double> V;
    for(int j=0;j < Data.size2(); j++) {
      V.push_back(Data(i,j));
    }
    sum_sum_score_deltas += cd.insert_row(V, i);
  }
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  std::cout << "sum_sum_score_deltas: " << sum_sum_score_deltas << std::endl;
  //
  sum_sum_score_deltas = 0;
  for(i=4; i < 8; i++) {
    std::vector<double> V;
    for(int j=0;j < Data.size2(); j++) {
      V.push_back(Data(i,j));
    }
    sum_sum_score_deltas += cd.insert_row(V, i);
  }
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  std::cout << "sum_sum_score_deltas: " << sum_sum_score_deltas << std::endl;
  //
  std::cout << std::endl << "logps" << std::endl;
  std::cout << cd.calc_logps() << std::endl;;
  std::cout << std::endl << "sum logp" << std::endl;
  std::cout << cd.calc_sum_logp() << std::endl;;
  //
  i = 8;
  std::vector<double> V;
  for(int j=0;j<Data.size2(); j++) {
    V.push_back(Data(i,j));
  }
  double vector_logp = cd.get_vector_logp(V);
  std::cout << "add vector with vector logp" << std::endl;
  std::cout << vector_logp << std::endl;
  cd.insert_row(V, i);
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  std::cout << "remove vector" << std::endl;
  cd.remove_row(V, i);
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  //
  std::cout << "calculate logps from scratch" << std::endl;
  std::cout << std::endl << "logps" << std::endl;
  std::cout << cd.calc_logps() << std::endl;;
  std::cout << std::endl << "sum logp" << std::endl;
  std::cout << cd.calc_sum_logp() << std::endl;;
  
  print_defaults();

  std::cout << "show use of underlying numerics functions" << std::endl;
  std::cout << "calc_continuous_logp(0, 1, 2, 2, 0)" << std::endl;
  std::cout << numerics::calc_continuous_logp(0, 1, 2, 2, 0) << std::endl;

  std::cout << "calc_cluster_crp_logp(10, 100, 10)" << std::endl;
  std::cout << numerics::calc_cluster_crp_logp(10, 100, 10) << std::endl;
  
  std::cout << std::endl << "Goodbye World!" << std::endl;
}
