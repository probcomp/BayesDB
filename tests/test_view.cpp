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

vector<double> extract_row(matrixD data, int row_idx) {
  vector<double> row;
  for(int j=0;j < data.size2(); j++) {
    row.push_back(data(row_idx, j));
  }
  return row;
}

void print_cluster_memberships(View& v) {
  cout << "Cluster memberships" << endl;
  set<Cluster<double>*>::iterator it = v.clusters.begin();
  for(; it!=v.clusters.end(); it++) {
    Cluster<double> &cd = **it;
    cout << cd.get_global_row_indices() << endl;
  }
  cout << "num clusters: " << v.get_num_clusters() << endl;

}

void insert_and_print(View& v, matrixD data,
		      int cluster_idx, int row_idx) {
  vector<double> row = extract_row(data, row_idx);
  Cluster<double>& cluster = v.get_cluster(cluster_idx);
  v.insert_row(row, cluster, row_idx);
  cout << "v.insert_row(" << row << ", " << cluster_idx << ", " \
	    << row_idx << ")" << endl;
  cout << "v.get_score(): " << v.get_score() << endl;
}

void remove_all_data(View &v, matrixD data) {
  set<Cluster<double>*>::iterator it = v.clusters.begin();
  for(; it!=v.clusters.end(); it++) {
    Cluster<double> &cd = **it;
    set<int> int_set = cd.get_global_row_indices();
    set<int>::iterator it2 = int_set.begin();
    for(; it2!=int_set.end(); it2++) {
      int idx_to_remove = *it2;
      vector<double> row = extract_row(data, idx_to_remove);
      v.remove_row(row, idx_to_remove);
    }
  }
  cout << "removed all data" << endl;
  v.print();
  //
  it = v.clusters.begin();
  it = v.clusters.begin();
  for(; it!=v.clusters.end(); it++) {
    v.remove_if_empty(**it);
  }
  cout << "removed empty clusters" << endl; 
  v.print();
}

int main(int argc, char** argv) {
  cout << endl << "Hello World!" << endl;

  // load some data
  matrixD data;
  LoadData("synthetic_data.csv", data);

  View v = View(data.size2(), 3);

  int row_idx, cluster_idx;
  row_idx = 0; cluster_idx = 0;
  insert_and_print(v, data, cluster_idx, row_idx);
  row_idx = 1; cluster_idx = 1;
  insert_and_print(v, data, cluster_idx, row_idx);
  row_idx = 2; cluster_idx = 0;
  insert_and_print(v, data, cluster_idx, row_idx);
  //
  row_idx = 3; cluster_idx = 1;
  insert_and_print(v, data, cluster_idx, row_idx);
  row_idx = 4; cluster_idx = 0;
  insert_and_print(v, data, cluster_idx, row_idx);
  row_idx = 5; cluster_idx = 1;
  insert_and_print(v, data, cluster_idx, row_idx);
  v.print();

  print_cluster_memberships(v);

  cout << "====================" << endl;
  cout << "Manually sampling" << endl;

  int num_vectors = v.get_num_vectors();
  cout << "num_vectors: " << v.get_num_vectors() << endl;

  map<int, vector<double> > data_map;
  for(int idx=0; idx<6; idx++) {
    vector<double> row = extract_row(data, idx);
    data_map[idx] = row;
  }

  RandomNumberGenerator rng = RandomNumberGenerator();
  for(int iter=0; iter<200; iter++) {
    print_cluster_memberships(v);
    v.transition_zs(data_map);
    cout << "Done iter: " << iter << endl;
    cout << endl;
  }
  
  remove_all_data(v, data);
  v.print();

  cout << endl << "Goodbye World!" << endl;
}
