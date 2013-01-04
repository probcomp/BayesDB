#include <iostream>
#include <algorithm>
#include <vector>
#include "Suffstats.h"
#include "RandomNumberGenerator.h"
#include "utils.h"

using namespace std;

typedef Suffstats<double> suffD;

bool is_almost(double val1, double val2, double precision) {
  return abs(val1-val2) < precision;
}

int main(int argc, char** argv) {  
  cout << "Begin:: test_suffstats" << endl;
  RandomNumberGenerator rng;

  // test settings
  int max_randi = 30;
  int num_values_to_test = 10;
  double precision = 1E-10;

  // generate all the random data to use
  //
  // initial parameters
  double r0 = rng.nexti(max_randi) * rng.next();
  double nu0 = rng.nexti(max_randi) * rng.next();
  double s0 = rng.nexti(max_randi) * rng.next();
  double mu0 = rng.nexti(max_randi) * rng.next();
  //
  // elements to add
  std::vector<double> values_to_test;
  for(int i=0; i<num_values_to_test; i++) {
    double rand_value = rng.nexti(max_randi) * rng.next();
    values_to_test.push_back(rand_value);
  }
  // remove in a different order
  std::vector<double> values_to_remove = values_to_test;
  std::random_shuffle(values_to_remove.begin(), values_to_remove.end());
  //
  // print values
  std::cout << "initial parameters: " << "\t";
  std::cout << "r0: " << r0 << "\t";
  std::cout << "nu0: " << nu0 << "\t";
  std::cout << "s0: " << s0 << "\t";
  std::cout << "mu0: " << mu0 << std::endl;
  std::cout << "values_to_test: " << values_to_test << std::endl;
  std::cout << "values_to_remove: " << values_to_remove << std::endl;

  // create the suffstats object
  //       r, nu, s, mu
  suffD sd(r0, nu0, s0, mu0);
  double score_0 = sd.get_score();
  cout << "initial suffstats object" << endl;
  cout << sd << endl;
  print_defaults();


  double insert_value;
  insert_value = 0.0;

  // verify initial parameters
  int count;
  double r, nu, s, mu;
  sd.get_suffstats(count, r, nu, s, mu);
  assert(count==0);
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), score_0, precision));

  // push data into suffstats
  for(std::vector<double>::iterator it=values_to_test.begin(); it!=values_to_test.end(); it++) {
    sd.insert_el(*it);
  }
  std::cout << "suffstats after insertion of data" << std::endl;
  cout << sd << endl;

  // ensure count is proper
  assert(sd.get_count()==num_values_to_test);

  // remove data from suffstats
  for(std::vector<double>::iterator it=values_to_remove.begin(); it!=values_to_remove.end(); it++) {
    sd.remove_el(*it);
  }
  std::cout << "suffstats after removal of data" << std::endl;
  cout << sd << endl;

  // ensure initial values are recovered
  sd.get_suffstats(count, r, nu, s, mu);
  assert(count==0);
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), score_0, precision));

  cout << "Stop:: test_suffstats" << endl;
}
