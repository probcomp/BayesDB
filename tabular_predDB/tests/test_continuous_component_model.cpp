/*
* Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*/
#include <iostream>
#include <algorithm>
#include <vector>
#include "ContinuousComponentModel.h"
#include "RandomNumberGenerator.h"
#include "utils.h"

using namespace std;

typedef ContinuousComponentModel CCM;

void insert_elements(CCM &ccm, vector<double> els) {
  for(vector<double>::iterator it=els.begin(); it!=els.end(); it++)
    ccm.insert_element(*it);
}

void remove_elements(CCM &ccm, vector<double> els) {
  for(vector<double>::iterator it=els.begin(); it!=els.end(); it++)
    ccm.remove_element(*it);
}

int main(int argc, char** argv) {  
  cout << endl << "Begin:: test_continuous_component_model" << endl;
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
  // to compare component models results with
 
  // create the component model object
  //
  //       r, nu, s, mu
  map<string, double> hypers;
  hypers["r"] = r0;
  hypers["nu"] = nu0;
  hypers["s"] = s0;
  hypers["mu"] = mu0;
  CCM ccm(hypers);
  cout << endl << "initial component model object" << endl;
  cout << ccm << endl;

  // verify initial parameters
  //
  int count;
  double sum_x, sum_x_sq;
  double r, nu, s, mu;
  ccm.get_suffstats(count, sum_x, sum_x_sq);
  ccm.get_hyper_doubles(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(ccm.calc_marginal_logp(), 0, precision));

  // push data into component model
  insert_elements(ccm, values_to_test);
  cout << endl << "component model after insertion of data" << endl;
  cout << ccm << endl;
  // ensure count is proper
  assert(ccm.get_count()==num_values_to_test);
  // remove data from component model in REVERSED order
  remove_elements(ccm, values_to_test_reversed);
  cout << endl << "component model after removal of data in reversed order" << endl;
  cout << ccm << endl;
  // ensure initial values are recovered
  ccm.get_suffstats(count, sum_x, sum_x_sq);
  ccm.get_hyper_doubles(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(ccm.calc_marginal_logp(), 0, precision));

  // push data into component model
  insert_elements(ccm, values_to_test);
  cout << endl << "component model after insertion of data" << endl;
  cout << ccm << endl;
  // ensure count is proper
  assert(ccm.get_count()==num_values_to_test);
  // remove data from component model in SHUFFLED order
  remove_elements(ccm, values_to_test_shuffled);
  cout << endl << "component model after removal of data in shuffled order" << endl;
  cout << ccm << endl;
  // ensure initial values are recovered
  ccm.get_suffstats(count, sum_x, sum_x_sq);
  ccm.get_hyper_doubles(r, nu, s, mu);
  assert(count==0);
  assert(is_almost(sum_x, 0, precision));
  assert(is_almost(sum_x_sq, 0, precision));
  assert(is_almost(r, r0, precision));
  assert(is_almost(nu, nu0, precision));
  assert(is_almost(s, s0, precision));
  assert(is_almost(mu, mu0, precision));
  assert(is_almost(ccm.calc_marginal_logp(), 0, precision));

  // push data into component model
  insert_elements(ccm, values_to_test);
  cout << endl << "component model after insertion of data" << endl;
  cout << ccm << endl;
  // test hypers
  int N_grid = 11;
  double test_scale = 10;
  ccm.get_suffstats(count, sum_x, sum_x_sq);
  ccm.get_hyper_doubles(r, nu, s, mu);
  double score_0 = ccm.calc_marginal_logp();
  vector<double> hyper_grid;
  vector<double> hyper_conditionals;
  double curr_hyper_conditional_in_grid;
  //
  //    test 'r' hyper
  cout << "testing r conditionals" << endl;
  hyper_grid = log_linspace(r / test_scale, r * test_scale, N_grid);
  hyper_conditionals = ccm.calc_hyper_conditionals("r", hyper_grid);
  cout << "r_grid from function: " << hyper_grid << endl;
  cout << "r_conditioanls from function: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr r conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 'nu' hyper
  cout << "testing nu conditionals" << endl;
  hyper_grid = log_linspace(nu / test_scale, nu * test_scale, N_grid);
  hyper_conditionals = ccm.calc_hyper_conditionals("nu", hyper_grid);
  cout << "nu_grid: " << hyper_grid << endl;
  cout << "nu_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr nu conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 's' hyper
  cout << "testing s conditionals" << endl;
  hyper_grid = log_linspace(s / test_scale, s * test_scale, N_grid);
  hyper_conditionals = ccm.calc_hyper_conditionals("s", hyper_grid);
  cout << "s_grid: " << hyper_grid << endl;
  cout << "s_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr s conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  //
  //    test 'mu' hyper
  cout << "testing mu conditionals" << endl;
  hyper_grid = log_linspace(mu / test_scale, mu * test_scale, N_grid);
  hyper_conditionals = ccm.calc_hyper_conditionals("mu", hyper_grid);
  cout << "mu_grid: " << hyper_grid << endl;
  cout << "mu_conditionals: " << hyper_conditionals << endl;
  curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
  cout << "curr  mu conditional in grid: " << curr_hyper_conditional_in_grid << endl;
  assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));

  // remove data from component model in SHUFFLED order
  remove_elements(ccm, values_to_test_shuffled);
  cout << endl << "component model after removal of data in shuffled order" << endl;
  cout << ccm << endl;

  // Test marginal_logp and predictive_logp analytically
  hypers["r"] = 9;
  hypers["nu"] = 17;
  hypers["s"] = 15;
  hypers["m"] = 13;
  CCM ccm2(hypers);
  values_to_test.clear();
  values_to_test.push_back(7);
  values_to_test.push_back(4);
  values_to_test.push_back(3);
  values_to_test.push_back(2);
  insert_elements(ccm2, values_to_test);
  assert(is_almost(ccm2.calc_marginal_logp(), -34.2990812968, precision));
  assert(is_almost(ccm2.calc_element_predictive_logp(7), -2.73018549043, precision));
  assert(is_almost(ccm2.calc_element_predictive_logp(4), -3.74794102225, precision));
  assert(is_almost(ccm2.calc_element_predictive_logp(3), -4.18966316516, precision));
  assert(is_almost(ccm2.calc_element_predictive_logp(2), -4.67271754595, precision));
  
  cout << "Stop:: test_component model" << endl;
}
