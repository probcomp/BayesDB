#ifndef GUARD_view_h
#define GUARD_view_h


#include <string>
#include <map>
#include <vector>
//
#include "RandomNumberGenerator.h"

#include "utils.h"
#include "Cluster.h"
#include "numerics.h"

//must forward declare
template <class T> class Cluster;

class View {
 public:
  View(int NUM_COLS, double CRP_ALPHA);
  // FIXME: will need to add a deallocator for clusters
  // for when View is garbage collected 
  double get_num_vectors() const;
  double get_num_cols() const;
  double get_score() const;
  //
  double insert_row(std::vector<double> vd, Cluster<double> &cd, int row_idx); 
  double remove_row(std::vector<double> vd, int row_idx); 
  double calc_cluster_vector_logp(std::vector<double> vd, Cluster<double> cd) const;
  std::vector<double> calc_cluster_vector_logps(std::vector<double> vd) const;
  Cluster<double>& get_cluster(int cluster_idx);
  /* Cluster<double> copy_cluster(int cluster_idx) const; */
  /* int get_cluster_location_idx(int row_idx); */
  /* Cluster<double>& get_cluster_location(int row_idx); */
  std::vector<int> get_cluster_counts() const;
  Cluster<double>& get_new_cluster();
  void remove_if_empty(Cluster<double>& which_cluster);
  std::set<Cluster<double>* > clusters;
  std::map<int, Cluster<double>* > cluster_lookup;
  double get_crp_score() const;
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
  void transition_z(std::vector<double> vd, int row_idx);
  /* void transition_crp_alpha(); */
  /* void transition_data_hypers(); */
  void print();
 private:
  double draw_rand_u();
  RandomNumberGenerator rng;
  double crp_alpha;
  double score;
  int num_clusters;
  int num_vectors;
  int num_cols;
  /* std::map<std::string, double> data_hypers; */
  /* void transition_vector(); */
  /* double get_data_hyper_score(); */
};


#endif //GUARD_view_h
