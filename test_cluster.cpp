#include <iostream>
#include "cluster.h"

int main(int argc, char** argv) {
  std::cout << std::endl << "Hello World!" << std::endl;
  int i = 123;

  cluster<double> cd(2);
  std::cout << std::endl << "Init cluster" << std::endl;
  std::cout << cd << std::endl;

  std::vector<double> vd0;
  vd0.push_back(1.0);
  vd0.push_back(10.0);
  cd.insert_row(vd0, 0);
  std::vector<double> vd1;
  vd1.push_back(2.0);
  vd1.push_back(20.0);
  cd.insert_row(vd1, 1);
  std::vector<double> vd2;
  vd2.push_back(3.0);
  vd2.push_back(30.0);
  cd.insert_row(vd2, 2);
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  //
  std::vector<double> vd3;
  vd3.push_back(3.0);
  vd3.push_back(30.0);
  cd.remove_row(vd3, 2);
  std::cout << std::endl << "modified cluster" << std::endl;
  std::cout << cd << std::endl;
  //
  print_defaults();

  std::map<int, double> logps = cd.calc_logps();
  std::cout << "logps: " << logps << std::endl;

  std::cout << std::endl << "Goodbye World!" << std::endl;
}
