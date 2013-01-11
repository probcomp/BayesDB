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

void print_cluster_memberships(View& v) {
  cout << "Cluster memberships" << endl;
  setCp_it it = v.clusters.begin();
  for(; it!=v.clusters.end(); it++) {
    Cluster &cd = **it;
    cout << cd.get_global_row_indices() << endl;
  }
  cout << "num clusters: " << v.get_num_clusters() << endl;
}

void insert_and_print(View& v, map<int, vector<double> > data_map,
		      int cluster_idx, int row_idx) {
  vector<double> row = data_map[row_idx];
  Cluster& cluster = v.get_cluster(cluster_idx);
  v.insert(row, cluster, row_idx);
  cout << "v.insert(" << row << ", " << cluster_idx << ", " \
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
    v.remove(row, idx_to_remove);
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
  cout << endl << "Hello World!" << endl;

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

  // create the view
  View v = View(data, 31);
  // print the initial view
  cout << "=============" << endl << "empty view print" << endl;
  v.print();
  cout << "empty view print" << endl << "=============" << endl;
  cout << endl;
  
  // populate the objects to test
  cout << endl << "populating objects" << endl;
  cout << "=================================" << endl;
  cout << "Insertings row:";
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    cout << " " << row_idx;
    vector<double> row = extract_row(data, row_idx);
    v.insert(row, row_idx);
  }
  cout << endl;
  cout << "=================================" << endl;
  cout << endl << "view after population" << endl;
  v.print();
  cout << "view after population" << endl;
  cout << "=================================" << endl;
  cout << endl;

  // print the clusters post population
  cout << endl << "view created clusters after population" << endl;
  for(setCp::iterator it=v.clusters.begin(); it!=v.clusters.end(); it++) {
    cout << **it << endl;
  }
  cout << endl;

  // print state info before transitioning
  print_cluster_memberships(v);
  int num_vectors = v.get_num_vectors();
  cout << "num_vectors: " << v.get_num_vectors() << endl;
  //
  cout << "====================" << endl;
  cout << "Sampling" << endl;

  // test transition
  RandomNumberGenerator rng = RandomNumberGenerator();
  for(int iter=0; iter<100; iter++) {
    v.assert_state_consistency();
    v.transition_zs(data_map);
    v.transition_crp_alpha();
    for(int col_idx=0; col_idx<num_cols; col_idx++) {
      v.transition_hypers(col_idx);
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

  cout << endl << "Goodbye World!" << endl;
}
