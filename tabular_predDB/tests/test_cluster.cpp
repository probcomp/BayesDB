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
#include "Cluster.h"
#include "utils.h"
#include "numerics.h"
#include "RandomNumberGenerator.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

using namespace std;

const static double r0_0 = 1.0;
const static double nu0_0 = 2.0;
const static double s0_0 = 2.0;
const static double mu0_0 = 0.0;

map<string, double> create_default_hypers() {
  map<string, double> hypers;
  hypers["r"] = r0_0;
  hypers["nu"] = nu0_0;
  hypers["s"] = s0_0;
  hypers["mu"] = mu0_0;
  return hypers;
}

int main(int argc, char** argv) {
  cout << "Begin:: test_cluster" << endl;
  RandomNumberGenerator rng;

  // set some test sizing parameters
  int max_value = 20;
  int num_rows = 3;
  int num_cols = 3;

  // create the objects
  map<int, map<string, double> > hypers_m;
  for(int i=0; i<num_cols; i++) {
    hypers_m[i] = create_default_hypers();
  }
  vector<map<string, double>*> hypers_v;
  map<int, map<string, double> >::iterator hm_it;
  for(hm_it=hypers_m.begin(); hm_it!=hypers_m.end(); hm_it++) {
    int key = hm_it->first;
    map<string, double> &hypers = hm_it->second;
    hypers_v.push_back(&hypers);
    cout << "hypers_" << key << ": " << hypers << endl;
  }
  cout << "hypers_v: " << hypers_v << endl;
  
  Cluster cd(hypers_v);
  vector<ComponentModel*> p_cm_v;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    ContinuousComponentModel *p_cm = new ContinuousComponentModel(*hypers_v[col_idx]);
    p_cm_v.push_back(p_cm);
  }

  // print the empty cluster
  cout << endl << endl <<"begin empty cluster print" << endl;
  cout << cd << endl;
  cout << "end empty cluster print" << endl << endl << endl;

  // generate random data;
  vector<vector<double> > rows;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    vector<double> row_data;
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      double random_value = (rng.nexti(max_value) + 1) * rng.next();
      row_data.push_back(random_value);
    }
    rows.push_back(row_data);
  }

  // poplute the objects
  cout << "Populating objects" << endl;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    vector<double> row_data = rows[row_idx];
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      double random_value = rows[row_idx][col_idx];
      p_cm_v[col_idx]->insert_element(random_value);
    }
    cd.insert_row(row_data, row_idx);
  }

  // test score equivalence
  vector<double> score_v;
  double sum_scores = 0;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    double suff_score = p_cm_v[col_idx]->calc_marginal_logp();
    score_v.push_back(suff_score);
    sum_scores += suff_score;
  }
  cout << "vector of separate suffstats scores after population: ";
  cout << score_v << endl;
  cout << "sum separate scores: " << sum_scores << endl;
  cout << "Cluster score with same data: " << cd.calc_sum_marginal_logps() << endl;
  cout << endl;
  //
  assert(is_almost(sum_scores, cd.calc_sum_marginal_logps(), 1E-10));



  // test hypers
  for(int which_col=0; which_col<num_cols; which_col++) {
    int N_grid = 11;
    double test_scale = 10;
    ContinuousComponentModel *p_ccm_i = dynamic_cast<ContinuousComponentModel*>(cd.p_model_v[which_col]);
    double r, nu, s, mu;
    double precision = 1E-10;
    p_ccm_i->get_hyper_doubles(r, nu, s, mu);
    double score_0 = p_ccm_i->calc_marginal_logp();
    vector<double> hyper_grid;
    vector<double> hyper_conditionals;
    double curr_hyper_conditional_in_grid;
    //
    //    test 'r' hyper
    cout << "testing r conditionals" << endl;
    hyper_grid = log_linspace(r / test_scale, r * test_scale, N_grid);
    hyper_conditionals = cd.calc_hyper_conditionals(which_col, "r", hyper_grid);
    cout << "r_grid from function: " << hyper_grid << endl;
    cout << "r_conditioanls from function: " << hyper_conditionals << endl;
    curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
    cout << "curr r conditional in grid: " << curr_hyper_conditional_in_grid << endl;
    assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));

    // map<string, double> &hypers = cd.get_hypers_i(which_col);
    map<string, double> &hypers = *(*cd.p_model_v[which_col]).p_hypers;
    double prior_r = hypers["r"];
    double new_r = hyper_grid[0]; 
    //
    cout << endl << "testing incorporate hyper update" << endl;
    cout << "new r: " << new_r << endl;
    hypers["r"] = new_r;
    cd.incorporate_hyper_update(which_col);
    cout << "marginal logp with new r: " << cd.p_model_v[which_col]->calc_marginal_logp() << endl;
    //
    cout << "changing r back to: " << prior_r << endl;
    hypers["r"] = prior_r;
    cd.incorporate_hyper_update(which_col);
    cout << "marginal logp with prior r: " << cd.p_model_v[which_col]->calc_marginal_logp() << endl;
    cout << "done testing incorporate hyper update on col" << endl << endl;

    //
    //    test 'nu' hyper
    cout << "testing nu conditionals" << endl;
    hyper_grid = log_linspace(nu / test_scale, nu * test_scale, N_grid);
    hyper_conditionals = cd.calc_hyper_conditionals(which_col, "nu", hyper_grid);
    cout << "nu_grid: " << hyper_grid << endl;
    cout << "nu_conditionals: " << hyper_conditionals << endl;
    curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
    cout << "curr nu conditional in grid: " << curr_hyper_conditional_in_grid << endl;
    assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
    //
    //    test 's' hyper
    cout << "testing s conditionals" << endl;
    hyper_grid = log_linspace(s / test_scale, s * test_scale, N_grid);
    hyper_conditionals = cd.calc_hyper_conditionals(which_col, "s", hyper_grid);
    cout << "s_grid: " << hyper_grid << endl;
    cout << "s_conditionals: " << hyper_conditionals << endl;
    curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
    cout << "curr s conditional in grid: " << curr_hyper_conditional_in_grid << endl;
    assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
    //
    //    test 'mu' hyper
    cout << "testing mu conditionals" << endl;
    hyper_grid = log_linspace(mu / test_scale, mu * test_scale, N_grid);
    hyper_conditionals = cd.calc_hyper_conditionals(which_col, "mu", hyper_grid);
    cout << "mu_grid: " << hyper_grid << endl;
    cout << "mu_conditionals: " << hyper_conditionals << endl;
    curr_hyper_conditional_in_grid = hyper_conditionals[(int)(N_grid-1)/2];
    cout << "curr  mu conditional in grid: " << curr_hyper_conditional_in_grid << endl;
    assert(is_almost(score_0, curr_hyper_conditional_in_grid, precision));
  }







  // depopulate the objects
  cout << "De-populating objects" << endl;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    vector<double> row_data = rows[row_idx];
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      double random_value = rows[row_idx][col_idx];
      p_cm_v[col_idx]->remove_element(random_value);
    }
    cd.remove_row(row_data, row_idx);
  }

  // test score equivalence
  score_v.clear();
  sum_scores = 0;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    double suff_score = p_cm_v[col_idx]->calc_marginal_logp();
    score_v.push_back(suff_score);
    sum_scores += suff_score;
  }
  cout << "vector of separate suffstats scores after depopulation: ";
  cout << score_v << endl;
  cout << "sum separate scores: " << sum_scores << endl;
  cout << "Cluster score with same data: " << cd.calc_sum_marginal_logps() << endl;
  cout << endl;
  //
  assert(is_almost(sum_scores, cd.calc_sum_marginal_logps(), 1E-10));

  // test ability to remove columns
  //
  // poplute the cluster object
  cout << "Populating objects" << endl;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    vector<double> row_data = rows[row_idx];
    cd.insert_row(row_data, row_idx);
  }
  cout << "cluster after population" << endl;
  cout << cd << endl;
  //
  // depopulate columns one by one
  while(cd.get_num_cols()>0) {
    int col_idx = cd.get_num_cols() - 1;
    cout << "removing column: " << col_idx << endl;
    cd.remove_col(col_idx);
    cout << "removed column: " << col_idx << endl;
    cout << "cluster now looks like: " << endl;
    cout << cd << endl;
  }

  while(p_cm_v.size()!=0) {
    ComponentModel *p_cm = p_cm_v.back();
    delete p_cm;
    p_cm_v.pop_back();
  }

  cout << "Stop:: test_cluster" << endl;
}
