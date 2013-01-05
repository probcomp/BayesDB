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
  //
  // getters (external use)
  double get_num_vectors() const;
  double get_num_cols() const;
  int get_num_clusters() const;
  double get_crp_score() const;
  double get_data_score() const;
  double get_score() const;
  double get_crp_alpha() const;
  /* double get_data_hyper_score(); */
  //
  // getters (internal use)
  Cluster<double>& get_cluster(int cluster_idx);
  std::vector<int> get_cluster_counts() const;
  //
  // calculators
  double calc_cluster_vector_logp(std::vector<double> vd, Cluster<double> cd, double &crp_logp_delta, double &data_logp_delta) const;
  std::vector<double> calc_cluster_vector_logps(std::vector<double> vd) const;
  double score_crp() const;
  std::vector<double> score_crp(std::vector<double> alphas) const;
  //
  // mutators
  double set_alpha(double new_alpha);
  Cluster<double>& get_new_cluster();
  double insert_row(std::vector<double> vd, Cluster<double> &cd, int row_idx); 
  double remove_row(std::vector<double> vd, int row_idx); 
  void remove_if_empty(Cluster<double>& which_cluster);
  void transition_z(std::vector<double> vd, int row_idx);
  void transition_zs(std::map<int, std::vector<double> > row_data_map);
  /* void transition_crp_alpha(); */
  /* void transition_data_hypers(); */
  //
  // data structures
  std::set<Cluster<double>* > clusters;
  std::map<int, Cluster<double>* > cluster_lookup;
  //
  // helper functions
  std::vector<int> shuffle_row_indices();
  void print();
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
 private:
  // parameters
  int num_vectors;
  int num_cols;
  double crp_alpha;
  double crp_score;
  double data_score;
  // data structures/sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max);
  /* std::map<std::string, double> data_hypers; */
};


#endif //GUARD_view_h
