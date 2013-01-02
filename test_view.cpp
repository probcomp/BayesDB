#include <iostream>
#include "Cluster.h"
#include "utils.h"
#include "numerics.h"
#include "View.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

typedef boost::numeric::ublas::matrix<double> matrixD;

std::vector<double> extract_row(matrixD data, int row_idx) {
  std::vector<double> row;
  for(int j=0;j < data.size2(); j++) {
    row.push_back(data(row_idx, j));
  }
  return row;
}

int main(int argc, char** argv) {
  std::cout << std::endl << "Hello World!" << std::endl;

  // load some data
  matrixD data;
  LoadData("SynData2.csv", data);

  View v = View(data.size2(), 10);

  for(int row_idx=0; row_idx<4; row_idx++) {
    std::vector<double> row = extract_row(data, row_idx);
    v.insert_row(row, 0, row_idx);
    std::cout << "v.insert_row(row, 0, row_idx)" << std::endl;
    std::cout << "v.get_score(): " << v.get_score() << std::endl;

  }

  int row_idx = 3;
  std::vector<double> row = extract_row(data, row_idx);
  v.remove_row(row, 0, row_idx);

  Cluster<double> cd = v.copy_cluster(0);

  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  std::cout << std::endl << "logps" << std::endl;
  std::cout << cd.calc_logps() << std::endl;;
  std::cout << std::endl << "sum logp" << std::endl;
  std::cout << cd.calc_sum_logp() << std::endl;;

  std::cout << "row" << std::endl;
  std::cout << row << std::endl;
  std::cout << "calc_cluster_vector_logp(row, 0)" << std::endl;
  std::cout << v.calc_cluster_vector_logp(row, 0) << std::endl;
  std::cout << "calc_cluster_vector_logps()" << std::endl;
  std::cout << v.calc_cluster_vector_logps(row) << std::endl;

  std::cout << std::endl << "Goodbye World!" << std::endl;
}
