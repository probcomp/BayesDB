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
  View(boost::numeric::ublas::matrix<double> data,
       std::vector<int> global_row_indices, std::vector<int> global_col_indices,
       int N_GRID=31);
  View();
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
  std::vector<double> get_hyper_grid(int global_col_idx, std::string which_hyper);
  /* double get_data_hyper_score(); */
  //
  // getters (internal use)
  Cluster& get_cluster(int cluster_idx);
  std::vector<int> get_cluster_counts() const;
  //
  // calculators
  double calc_cluster_vector_predictive_logp(std::vector<double> vd, Cluster cd,
					     double &crp_logp_delta,
					     double &data_logp_delta) const;
  std::vector<double> calc_cluster_vector_predictive_logps(std::vector<double> vd) const;
  double calc_crp_marginal() const;
  std::vector<double> calc_crp_marginals(std::vector<double> alphas) const;
  std::vector<double> calc_hyper_conditionals(int which_col,
					      std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  double calc_column_predictive_logp(std::vector<double> column_data,
				     std::vector<int> data_global_row_indices);
  //
  // mutators
  double set_alpha(double new_alpha);
  Cluster& get_new_cluster();
  double insert_row(std::vector<double> vd, Cluster &cd, int row_idx);
  double insert_row(std::vector<double> vd, int row_idx);
  double remove_row(std::vector<double> vd, int row_idx); 
  double remove_col(int col_idx);
  double insert_col(std::vector<double> data,
		    std::vector<int> data_global_row_indices,
		    int global_col_idx);
  void remove_if_empty(Cluster& which_cluster);
  double transition_z(std::vector<double> vd, int row_idx);
  double transition_zs(std::map<int, std::vector<double> > row_data_map);
  double transition_crp_alpha();
  double set_hyper(int which_col, std::string which_hyper, double new_value);
  double transition_hyper_i(int which_col, std::string which_hyper,
			  std::vector<double> hyper_grid);
  double transition_hyper_i(int which_col, std::string which_hyper);
  double transition_hypers_i(int which_col);
  double transition_hypers();
  double transition(std::map<int, std::vector<double> > row_data_map);
  //
  // data structures
  std::set<Cluster* > clusters;
  std::map<int, Cluster* > cluster_lookup;
  //
  // helper functions
  std::vector<double> align_data(std::vector<double> values,
				 std::vector<int> global_column_indices) const;
  std::vector<int> shuffle_row_indices();
  void print();
  void print_score_matrix();
  void assert_state_consistency();
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
  //
  // hyper inference grids FIXME: MOVE TO PRIVATE WHEN DONE TESTING
  std::vector<double> crp_alpha_grid;
  std::vector<double> r_grid;
  std::vector<double> nu_grid;
  std::map<int, std::vector<double> > s_grids;
  std::map<int, std::vector<double> > mu_grids;
  std::map<int, int> global_to_local; // FIXME: specify appicability to columns
 private:
  // parameters
  double crp_alpha;
  double crp_score;
  double data_score;
  // sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max);
  // helpers
  void construct_hyper_grids(boost::numeric::ublas::matrix<double> data,
			     std::vector<int> col_indices, int N_GRID);
  /* std::map<std::string, double> data_hypers; */
};

#endif //GUARD_view_h
