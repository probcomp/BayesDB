#include <iostream>
#include <algorithm>
#include <vector>
#include "Suffstats.h"
#include "RandomNumberGenerator.h"
#include "utils.h"

using namespace std;

typedef Suffstats<double> suffD;

void insert_els(Suffstats<double> &sd, vector<double> els) {
  for(vector<double>::iterator it=els.begin(); it!=els.end(); it++)
    sd.insert_el(*it);
}

void remove_els(Suffstats<double> &sd, vector<double> els) {
  for(vector<double>::iterator it=els.begin(); it!=els.end(); it++)
    sd.remove_el(*it);
}

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

  // FIXME: should compare with a fixed dataset with known 
  // post-update hyper values and score

  // FIXME: should be manually calling numerics:: functions
  // to compare suffstats results with
 
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
  double sum_x, sum_x_sq;
  double r, nu, s, mu;
  sd.get_suffstats(count, sum_x, sum_x_sq);
  sd.get_hypers(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  // push data into suffstats
  insert_els(sd, values_to_test);
  cout << endl << "suffstats after insertion of data" << endl;
  cout << sd << endl;
  // ensure count is proper
  assert(sd.get_count()==num_values_to_test);
  // remove data from suffstats in REVERSED order
  remove_els(sd, values_to_test_reversed);
  cout << endl << "suffstats after removal of data in reversed order" << endl;
  cout << sd << endl;
  // ensure initial values are recovered
  sd.get_suffstats(count, sum_x, sum_x_sq);
  sd.get_hypers(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  // push data into suffstats
  insert_els(sd, values_to_test);
  cout << endl << "suffstats after insertion of data" << endl;
  cout << sd << endl;
  // ensure count is proper
  assert(sd.get_count()==num_values_to_test);
  // remove data from suffstats in SHUFFLED order
  remove_els(sd, values_to_test_shuffled);
  cout << endl << "suffstats after removal of data in shuffled order" << endl;
  cout << sd << endl;
  // ensure initial values are recovered
  sd.get_suffstats(count, sum_x, sum_x_sq);
  sd.get_hypers(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(sd.get_score(), 0, precision));

  // push data into suffstats
  insert_els(sd, values_to_test);
  cout << endl << "suffstats after insertion of data" << endl;
  cout << sd << endl;
  // test hypers
  int N_grid = 11;
  double test_scale = 10;
  sd.get_suffstats(count, sum_x, sum_x_sq);
  sd.get_hypers(r, nu, s, mu);
  double score_0 = sd.get_score();
  vector<double> hyper_grid;
  vector<double> hyper_conditionals;
  double curr_hyper_conditional_in_grid;
  //
  //    test 'r' hyper
  cout << "testing r conditionals" << endl;
  hyper_grid = log_linspace(r / test_scale, r * test_scale, N_grid);
  hyper_conditionals = \
    numerics::calc_continuous_r_conditionals(hyper_grid, count, sum_x, sum_x_sq,
					     nu, s, mu);
  cout << "hyper_grid: " << hyper_grid << endl;
  cout << "hyper_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr hyper conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 'nu' hyper
  cout << "testing nu conditionals" << endl;
  hyper_grid = log_linspace(nu / test_scale, nu * test_scale, N_grid);
  hyper_conditionals = \
    numerics::calc_continuous_nu_conditionals(hyper_grid, count, sum_x, sum_x_sq,
					      r, s, mu);
  cout << "hyper_grid: " << hyper_grid << endl;
  cout << "hyper_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr hyper conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 's' hyper
  cout << "testing s conditionals" << endl;
  hyper_grid = log_linspace(s / test_scale, s * test_scale, N_grid);
  hyper_conditionals = \
    numerics::calc_continuous_s_conditionals(hyper_grid, count, sum_x, sum_x_sq,
					     r, nu, mu);
  cout << "hyper_grid: " << hyper_grid << endl;
  cout << "hyper_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr hyper conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 'mu' hyper
  cout << "testing mu conditionals" << endl;
  hyper_grid = log_linspace(mu / test_scale, mu * test_scale, N_grid);
  hyper_conditionals = \
    numerics::calc_continuous_mu_conditionals(hyper_grid, count, sum_x, sum_x_sq,
					      r, nu, s);
  cout << "hyper_grid: " << hyper_grid << endl;
  cout << "hyper_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr hyper conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));

  // remove data from suffstats in SHUFFLED order
  remove_els(sd, values_to_test_shuffled);
  cout << endl << "suffstats after removal of data in shuffled order" << endl;
  cout << sd << endl;

  
  cout << "Stop:: test_suffstats" << endl;
}
