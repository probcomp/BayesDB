#include <iostream>
#include <algorithm>
#include <vector>
#include "Suffstats.h"
#include "RandomNumberGenerator.h"
#include "utils.h"

using namespace std;

typedef Suffstats<double> suffD;

int main(int argc, char** argv) {  
  cout << endl << "Begin:: test_suffstats" << endl;
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
  vector<double> values_to_test;
  for(int i=0; i<num_values_to_test; i++) {
    double rand_value = rng.nexti(max_randi) * rng.next();
    values_to_test.push_back(rand_value);
  }
  // remove in a reversed order and a different order
  vector<double> values_to_test_reversed = values_to_test;
  std::reverse(values_to_test_reversed.begin(), values_to_test_reversed.end());
  vector<double> values_to_test_shuffled = values_to_test;
  std::random_shuffle(values_to_test_shuffled.begin(), values_to_test_shuffled.end());

  // print generated values
  //
  cout << endl << "initial parameters: " << "\t";
  cout << "r0: " << r0 << "\t";
  cout << "nu0: " << nu0 << "\t";
  cout << "s0: " << s0 << "\t";
  cout << "mu0: " << mu0 << endl;
  cout << "values_to_test: " << values_to_test << endl;
  cout << "values_to_test_shuffled: " << values_to_test_shuffled << endl;

  // create the suffstats object
  //
  //       r, nu, s, mu
  suffD sd(r0, nu0, s0, mu0);
  cout << endl << "initial suffstats object" << endl;
  cout << sd << endl;
  //
  print_defaults();

  // verify initial parameters
  //
  int count;
  double r, nu, s, mu;
  sd.get_suffstats(count, r, nu, s, mu);
  assert(count==0);
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  // push data into suffstats
  for(vector<double>::iterator it=values_to_test.begin(); it!=values_to_test.end(); it++) {
    sd.insert_el(*it);
  }
  cout << endl << "suffstats after insertion of data" << endl;
  cout << sd << endl;
  // ensure count is proper
  assert(sd.get_count()==num_values_to_test);
  // remove data from suffstats in REVERSED order
  for(vector<double>::iterator it=values_to_test_reversed.begin(); it!=values_to_test_reversed.end(); it++) {
    sd.remove_el(*it);
  }
  cout << endl << "suffstats after removal of data in reversed order" << endl;
  cout << sd << endl;
  // ensure initial values are recovered
  sd.get_suffstats(count, r, nu, s, mu);
  assert(count==0);
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  // push data into suffstats
  for(vector<double>::iterator it=values_to_test.begin(); it!=values_to_test.end(); it++) {
    sd.insert_el(*it);
  }
  cout << endl << "suffstats after insertion of data" << endl;
  cout << sd << endl;
  // ensure count is proper
  assert(sd.get_count()==num_values_to_test);
  // remove data from suffstats in SHUFFLED order
  for(vector<double>::iterator it=values_to_test_shuffled.begin(); it!=values_to_test_shuffled.end(); it++) {
    sd.remove_el(*it);
  }
  cout << endl << "suffstats after removal of data in shuffled order" << endl;
  cout << sd << endl;
  // ensure initial values are recovered
  sd.get_suffstats(count, r, nu, s, mu);
  assert(count==0);
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  cout << "Stop:: test_suffstats" << endl;
}
