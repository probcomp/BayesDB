#ifndef GUARD_view_h
#define GUARD_view_h


#include <string>
#include <map>
#include <vector>
#include <assert.h>
#include <numeric> // std::accumulate
//
#include "RandomNumberGenerator.h"
#include "utils.h"
#include "Cluster.h"
#include "numerics.h"

class Cluster;

class View {
 public:
  //FIXME: add constructor with ranges as arguments, rather than recalculate
  View(boost::numeric::ublas::matrix<double> data, int N_GRID=31);
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
  std::vector<std::string> get_hyper_strings();
  std::map<std::string, double> get_hypers(int col_idx);
  std::vector<double> get_hyper_grid(int which_col, std::string which_hyper);
  /* double get_data_hyper_score(); */
  //
  // getters (internal use)
  Cluster& get_cluster(int cluster_idx);
  std::vector<int> get_cluster_counts() const;
  //
  // calculators
  double calc_cluster_vector_logp(std::vector<double> vd, Cluster cd, double &crp_logp_delta, double &data_logp_delta) const;
  std::vector<double> calc_cluster_vector_logps(std::vector<double> vd) const;
  double score_crp() const;
  std::vector<double> score_crp(std::vector<double> alphas) const;
  std::vector<double> calc_hyper_conditionals(int which_col, std::string which_hyper, std::vector<double> hyper_grid) const;
  //
  // mutators
  double set_alpha(double new_alpha);
  Cluster& get_new_cluster();
  double insert(std::vector<double> vd, Cluster &cd, int row_idx);
  double insert(std::vector<double> vd, int row_idx);
  double remove(std::vector<double> vd, int row_idx); 
  void remove_if_empty(Cluster& which_cluster);
  void transition_z(std::vector<double> vd, int row_idx);
  void transition_zs(std::map<int, std::vector<double> > row_data_map);
  void transition_crp_alpha();
  double set_hyper(int which_col, std::string which_hyper, double new_value);
  void transition_hyper(int which_col, std::string which_hyper, std::vector<double> hyper_grid);
  void transition_hyper(int which_col, std::string which_hyper);
  void transition_hypers(int which_col);
  /* void transition_data_hypers(); */
  //
  // data structures
  std::set<Cluster* > clusters;
  std::map<int, Cluster* > cluster_lookup;
  //
  // helper functions
  std::vector<int> shuffle_row_indices();
  void print();
  void assert_state_consistency();
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
  //
  // hyper inference grids FIXME: MOVE TO PRIVATE WHEN DONE TESTING
  std::vector<double> crp_alpha_grid;
  std::vector<double> r_grid;
  std::vector<double> nu_grid;
  std::vector<std::vector<double> > s_grids;
  std::vector<std::vector<double> > mu_grids;
 private:
  // parameters
  int num_vectors;
  int num_cols;
  double crp_alpha;
  double crp_score;
  double data_score;
  // sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max);
  /* std::map<std::string, double> data_hypers; */
};

#endif //GUARD_view_h
