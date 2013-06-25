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
#include "constants.h"
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

void print_with_header(View &v, string header) {
  cout << endl;
  cout << "=================================" << endl;
  cout << header << endl;
  v.print();
  cout << header << endl;
  cout << "=================================" << endl;
  cout << endl;
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
  cout << endl << "test_view_speed: Hello World!" << endl;

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

  // create the view
  int N_GRID = 31;
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

  // print the initial view
  print_with_header(v, "empty view print");


  cout << "insert a single row (1):";
  int row_idx = 0;
  vector<double> row = extract_row(data, row_idx);
  v.insert_row(row, row_idx);
  print_with_header(v, "view after inserting single row (1)");

  cout << "remove a single row (1):";
  row_idx = 0;
  row = extract_row(data, row_idx);
  v.remove_row(row, row_idx);
  print_with_header(v, "view after removeing single row (1)");

  cout << "printing cluster row_indices" << endl;
  for(int cluster_idx=0; cluster_idx<v.get_num_clusters(); cluster_idx++) {
    Cluster c = v.get_cluster(cluster_idx);
    cout << "cluster has row_indices: " << c.get_row_indices_set() << endl;
  }
  cout << "DONE printing cluster row_indices" << endl;

  // populate the objects to test
  cout << endl << "populating objects" << endl;
  cout << "=================================" << endl;
  cout << "Insertings row:";
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    cout << " " << row_idx;
    vector<double> row = extract_row(data, row_idx);
    v.insert_row(row, row_idx);
  }
  print_with_header(v, "view after population");

  cout << "====================" << endl;
  cout << "Sampling" << endl;
  // test transition
  RandomNumberGenerator rng = RandomNumberGenerator();
  for(int iter=0; iter<21; iter++) {
    v.assert_state_consistency();
    v.transition_zs(data_map);
    v.transition_crp_alpha();
    v.transition_hypers();
    if(iter % 10 == 0) {
      cout << "Done iter: " << iter << endl;
      print_with_header(v, "view after iter");
    }
  }
  cout << "Done transition_zs" << endl;
  cout << endl;
  v.print();
  v.print_score_matrix();
  cout << "v.global_to_local: " << v.global_to_local << endl;

  int remove_col_idx, insert_col_idx;
  remove_col_idx = 2;
  insert_col_idx = 2;
  vector<double> col_data = extract_col(data, insert_col_idx);
  vector<int> data_global_row_indices = create_sequence(col_data.size(), 0);
  double score_delta_1, score_delta_2, score_0, score_1;

  cout << "=====================" << endl;
  cout << "=====================" << endl;
  cout << "=====================" << endl;
  remove_col_idx = 2;
  cout << "removing column: " << remove_col_idx;
  v.remove_col(remove_col_idx);
  cout << "FLAG:: score: " << v.get_score() << endl;
  v.print_score_matrix();
  cout << "v.global_to_local: " << v.global_to_local << endl;

  cout << "=====================" << endl;
  cout << "=====================" << endl;
  cout << "=====================" << endl;
  insert_col_idx = remove_col_idx;
  cout << "inserting column: " << insert_col_idx;
  score_0 = v.get_score();
  score_delta_1 = v.calc_column_predictive_logp(col_data, CONTINUOUS_DATATYPE, data_global_row_indices, hypers_m[insert_col_idx]);
  score_delta_2 = v.insert_col(col_data, data_global_row_indices, insert_col_idx, hypers_m[insert_col_idx]);
  score_1 = v.get_score();
  cout << "FLAG:: " << "score_0: " << score_0 << ", score_1: " << score_1;
  cout << ", score_delta_1: " << score_delta_1 << ", score_delta_2: " << score_delta_2 << endl;

  v.print_score_matrix();
  cout << "v.global_to_local: " << v.global_to_local << endl;

  cout << "=====================" << endl;
  cout << "=====================" << endl;
  cout << "=====================" << endl;
  remove_col_idx = 2;
  cout << "removing column: " << remove_col_idx;
  v.remove_col(remove_col_idx);
  cout << "FLAG:: score: " << v.get_score() << endl;
  v.print_score_matrix();
  cout << "v.global_to_local: " << v.global_to_local << endl;

  cout << "=====================" << endl;
  cout << "=====================" << endl;
  cout << "=====================" << endl;
  insert_col_idx = 2;
  cout << "inserting column: " << insert_col_idx;
  v.insert_col(col_data, data_global_row_indices, insert_col_idx, hypers_m[insert_col_idx]);
  cout << "FLAG:: score: " << v.get_score() << endl;
  v.print_score_matrix();
  cout << "v.global_to_local: " << v.global_to_local << endl;

  v.print();
  // empty object and verify empty
  remove_all_data(v, data_map);
  v.print();

  cout << "insert a single row (2): " << flush;
  row_idx = 0;
  row = extract_row(data, row_idx);

  vector<int> global_indices = create_sequence(row.size());
  vector<double> aligned_row = v.align_data(row, global_indices);

  cout << aligned_row << endl << flush;
  v.insert_row(aligned_row, row_idx);
  print_with_header(v, "view after inserting single row (2)");

  cout << "remove a single row (2):";
  v.remove_row(aligned_row, row_idx);
  print_with_header(v, "view after removeing single row (2)");

  cout << endl << "test_view_speed: Goodbye World!" << endl;
}
