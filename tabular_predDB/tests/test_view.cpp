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
#include "View.h"
#include "RandomNumberGenerator.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

typedef boost::numeric::ublas::matrix<double> matrixD;
using namespace std;
typedef vector<Cluster*> vectorCp;
typedef set<Cluster*> setCp;
typedef map<int, Cluster*> mapICp;
typedef setCp::iterator setCp_it;
typedef mapICp::iterator mapICp_it;
typedef vector<int>::iterator vectorI_it;

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

void print_cluster_memberships(View& v) {
  cout << "Cluster memberships" << endl;
  setCp_it it = v.clusters.begin();
  for(; it!=v.clusters.end(); it++) {
    Cluster &cd = **it;
    cout << cd.get_row_indices_set() << endl;
  }
  cout << "num clusters: " << v.get_num_clusters() << endl;

}

void insert_and_print(View& v, map<int, vector<double> > data_map,
		      int cluster_idx, int row_idx) {
  vector<double> row = data_map[row_idx];
  Cluster& cluster = v.get_cluster(cluster_idx);
  v.insert_row(row, cluster, row_idx);
  cout << "v.insert(" << row << ", " << cluster_idx << ", "	\
	    << row_idx << ")" << endl;
  cout << "v.get_score(): " << v.get_score() << endl;
}

void remove_all_data(View &v, map<int, vector<double> > data_map) {
  vector<int> rows_in_view;
  for(mapICp_it it=v.cluster_lookup.begin(); it!=v.cluster_lookup.end(); it++) {
    rows_in_view.push_back(it->first);
  }
  for(vectorI_it it=rows_in_view.begin(); it!=rows_in_view.end(); it++) {
    int idx_to_remove = *it;
    vector<double> row = data_map[idx_to_remove];
    vector<int> global_indices = create_sequence(row.size());
    vector<double> aligned_row = v.align_data(row, global_indices);
    v.remove_row(aligned_row, idx_to_remove);
  }
  cout << "removed all data" << endl;
  v.print();
  //
  for(setCp_it it=v.clusters.begin(); it!=v.clusters.end(); it++) {
    v.remove_if_empty(**it);
  }
  assert(v.get_num_vectors()==0);
  assert(v.get_num_clusters()==0);
  cout << "removed empty clusters" << endl; 
  v.print();
}

int main(int argc, char** argv) {
  cout << endl << "test_view: Hello World!" << endl;

  // load some data
  matrixD data;
  LoadData("SynData2.csv", data);
  int num_cols = data.size2();
  int num_rows = data.size1();
  //
  map<int, vector<double> > data_map;
  cout << "populating data_map" << endl;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    data_map[row_idx] = extract_row(data, row_idx);
  }
  //
  map<int, int> where_to_push;
  where_to_push[0] = 0;
  where_to_push[1] = 1;
  where_to_push[2] = 0;
  where_to_push[3] = 1;
  where_to_push[4] = 0;
  where_to_push[5] = 1;
  //
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

  set<int> cluster_idx_set;
  for(map<int,int>::iterator it=where_to_push.begin(); it!=where_to_push.end(); it++) {
    int cluster_idx = it->second;
    cluster_idx_set.insert(cluster_idx);
  }

  // create the objects to test
  int N_GRID = 11;
  int SEED = 0;
  vector<int> global_row_indices = create_sequence(data.size1());
  vector<int> global_column_indices = create_sequence(data.size2());
  // construct hyper grids
  vector<double> row_crp_alpha_grid = create_crp_alpha_grid(num_rows, N_GRID);
  vector<double> r_grid;
  vector<double> nu_grid;
  map<int, vector<double> > s_grids;
  map<int, vector<double> > mu_grids;
  construct_continuous_base_hyper_grids(N_GRID, num_rows, r_grid, nu_grid);
  for(vector<int>::iterator it=global_column_indices.begin(); it!=global_column_indices.end(); it++) {
    int global_col_idx = *it;
    vector<double> col_data = extract_col(data, global_col_idx);
    construct_continuous_specific_hyper_grid(N_GRID, col_data,
					     s_grids[global_col_idx],
					     mu_grids[global_col_idx]);
  }

  map<int, string> global_col_types;
  for(int i=0; i<global_column_indices.size(); i++) {
    global_col_types[i] = CONTINUOUS_DATATYPE;
  }
  vector<double> multinomial_alpha_grid = \
    log_linspace(1., num_rows, N_GRID);
  View v = View(data, global_col_types,
		global_row_indices, global_column_indices, hypers_m,
		row_crp_alpha_grid, multinomial_alpha_grid,
		r_grid, nu_grid, s_grids, mu_grids,
		SEED);

  v.print();
  // empty object and verify empty
  remove_all_data(v, data_map);
  v.print();

  v.print();
  v.assert_state_consistency();
  //
  vectorCp cd_v;
  for(set<int>::iterator it=cluster_idx_set.begin(); it!=cluster_idx_set.end(); it++) {
    int cluster_idx = *it;
    cout << "inserting cluster idx: " << cluster_idx << endl;
    Cluster *p_cd = new Cluster(hypers_v);
    cd_v.push_back(p_cd);
  }

  // print the initial view
  cout << "empty view print" << endl;
  v.print();
  cout << "empty view print" << endl;
  cout << endl;
  
  // populate the objects to test
  cout << endl << "populating objects" << endl;
  cout << "=================================" << endl;
  for(map<int,int>::iterator it=where_to_push.begin(); it!=where_to_push.end(); it++) {
    v.assert_state_consistency();
    int row_idx = it->first;
    int cluster_idx = it->second;
    cout << "INSERTING ROW: " << row_idx << endl;
    insert_and_print(v, data_map, cluster_idx, row_idx);
    Cluster *p_cd = cd_v[cluster_idx];
    double cluster_score_delta = (*p_cd).insert_row(data_map[row_idx], row_idx);
    cout << "cluster_score_delta: " << cluster_score_delta << endl;
    cout << "DONE INSERTING ROW: " << row_idx << endl;
  }
  cout << endl << "view after population" << endl;
  v.print();
  cout << "view after population" << endl;
  cout << "=================================" << endl;
  cout << endl;

  // print the clusters post population
  cout << endl << "separately created clusters after population" << endl;
  for(vectorCp::iterator it=cd_v.begin(); it!=cd_v.end(); it++) {
    cout << **it << endl;
  }
  cout << endl;

  // independently verify view score as sum of data and crp scores
  vector<double> cluster_scores;
  setCp_it it = v.clusters.begin();
  double sum_scores = 0;
  for(; it!=v.clusters.end(); it++) {
    double cluster_score = (*it)->calc_sum_marginal_logps();
    cluster_scores.push_back(cluster_score);
    sum_scores += cluster_score;
  }
  vector<int> cluster_counts = v.get_cluster_counts();
  double crp_score = numerics::calc_crp_alpha_conditional(cluster_counts,
							  v.get_crp_alpha(),
							  -1, true);
  double crp_plus_data_score = crp_score + sum_scores;
  cout << "vector of cluster scores: " << cluster_scores << endl;
  cout << "sum cluster scores: " << sum_scores << endl;
  cout << "crp score: " << crp_score << endl;
  cout << "sum cluster scores and crp score: " << crp_plus_data_score << endl;
  cout << "view score: " << v.get_score() << endl;
  assert(is_almost(v.get_score(), crp_plus_data_score, 1E-10));

  // test crp alpha hyper inference
  vector<double> test_alphas;
  test_alphas.push_back(.3);
  test_alphas.push_back(3.);
  test_alphas.push_back(30.);
  cluster_counts = v.get_cluster_counts();  
  vector<double> test_alpha_scores;
  for(vector<double>::iterator it=test_alphas.begin(); it!=test_alphas.end(); it++) {
    double test_alpha_score = numerics::calc_crp_alpha_conditional(cluster_counts, *it, -1, true);
    test_alpha_scores.push_back(test_alpha_score);
    v.assert_state_consistency();
  }
  cout << "test_alphas: " << test_alphas << endl;
  cout << "test_alpha_scores: " << test_alpha_scores << endl;
  double new_alpha = test_alphas[0];
  double crp_score_delta = v.set_crp_alpha(new_alpha);
  cout << "new_alpha: " << new_alpha << ", new_alpha score: " << v.get_crp_score() << ", crp_score_delta: " << crp_score_delta << endl;
  new_alpha = test_alphas[1];
  crp_score_delta = v.set_crp_alpha(new_alpha);
  cout << "new_alpha: " << new_alpha << ", new_alpha score: " << v.get_crp_score() << ", crp_score_delta: " << crp_score_delta << endl;

  // test continuous data hyper conditionals
  vector<double> hyper_grid;
  vector<double> hyper_logps;
  vector<string> hyper_strings;
  hyper_strings.push_back("r");  hyper_strings.push_back("nu");  hyper_strings.push_back("s");  hyper_strings.push_back("mu");
  map<string, double> default_hyper_values;
  default_hyper_values["r"] = 1.0; default_hyper_values["nu"] = 2.0; default_hyper_values["s"] = 2.0; default_hyper_values["mu"] = 0.0;
  for(vector<string>::iterator it = hyper_strings.begin(); it!=hyper_strings.end(); it++) {
    vector<double> curr_r_conditionals;
    string hyper_string = *it;
    double default_value = default_hyper_values[hyper_string];
    cout << endl;
    cout << hyper_string << " hyper conditionals" << endl;
    cout << "num_cols: " << num_cols << endl;
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      hyper_grid = v.get_hyper_grid(col_idx, hyper_string);
      cout << hyper_string << " grid: " << hyper_grid << endl;
      hyper_logps = v.calc_hyper_conditionals(col_idx, hyper_string, hyper_grid);
      cout << "conditionals: " << hyper_logps << endl;
      double curr_r_conditional = hyper_logps[(int)(N_GRID-1)/2];
      curr_r_conditionals.push_back(curr_r_conditional);
      cout << "curr conditional: " << curr_r_conditional << endl;
    }
    double sum_curr_conditionals = std::accumulate(curr_r_conditionals.begin(),curr_r_conditionals.end(),0.);
    cout << "sum curr conditionals: " << sum_curr_conditionals << endl;
  }

  // test continuous data hyper inference
  // verify setting results in predicted delta
  cout << endl;
  cout << endl;
  string hyper_string = "r";
  double default_value = default_hyper_values[hyper_string];
  //
  hyper_grid = v.get_hyper_grid(0, "r");
  int col_idx = 0;
  vector<double> unorm_logps = v.calc_hyper_conditionals(col_idx, hyper_string, hyper_grid);
  double curr_conditional = unorm_logps[(int)(N_GRID-1)/2];
  double curr_data_score = v.get_data_score();
  //
  cout << "hyper_grid: " << hyper_grid << endl;
  cout << "unorm_logps: " << unorm_logps << endl;
  vector<double> score_deltas = unorm_logps;
  for(vector<double>::iterator it=score_deltas.begin(); it!=score_deltas.end(); it++) {
    *it -= curr_conditional;
  }
  cout << "score_deltas: " << score_deltas << endl;
  double data_score_0 = v.get_data_score();
  for(int grid_idx=0; grid_idx<hyper_grid.size(); grid_idx++) {
    double new_hyper_value = hyper_grid[grid_idx];
    v.set_hyper(col_idx, hyper_string, new_hyper_value);
    double new_data_score = v.get_data_score();
    double data_score_delta = new_data_score - data_score_0;
    cout << "hyper_value: " << new_hyper_value << ", data_score: " << new_data_score << ", data_score_delta: " << data_score_delta << endl;
  }

  
  // print state info before transitioning
  print_cluster_memberships(v);
  int num_vectors = v.get_num_vectors();
  cout << "num_vectors: " << v.get_num_vectors() << endl;
  //
  cout << "====================" << endl;
  cout << "Sampling" << endl;

  // test transition
  RandomNumberGenerator rng = RandomNumberGenerator();
  for(int iter=0; iter<21; iter++) {
    v.assert_state_consistency();
    v.transition_zs(data_map);
    v.transition_crp_alpha();
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      std::random_shuffle(hyper_strings.begin(), hyper_strings.end());
      for(vector<string>::iterator it=hyper_strings.begin(); it!=hyper_strings.end(); it++) {
	string hyper_string = *it;
	v.transition_hyper_i(col_idx,hyper_string);
      }
    }
    // if(iter % 10 == 0) {
    if(iter % 1 == 0) {
      print_cluster_memberships(v);
      for(int col_idx=0; col_idx<num_cols; col_idx++) {
	cout << "Hypers(col_idx=" << col_idx <<"): " << v.get_hypers(col_idx) << endl;
      }
      cout << "score: " << v.get_score() << endl;
      cout << "Done iter: " << iter << endl;
      cout << endl;
    }
  }
  print_cluster_memberships(v);
  cout << "Done transition_zs" << endl;
  cout << endl;

  // empty object and verify empty
  remove_all_data(v, data_map);
  v.print();

  // FIXME: still have a data score!?

  for(vectorCp::iterator it = cd_v.begin(); it!=cd_v.end(); it++) {
    Cluster *p_c = (*it);
    while(p_c->get_count()!=0) {
      vector<int> row_indices = p_c->get_row_indices_vector();
      int row_idx = row_indices[0];
      p_c->remove_row(data_map[row_idx], row_idx);
    }
    p_c->delete_component_models();
    delete p_c;
  }

  cout << endl << "test_view: Goodbye World!" << endl;
}
