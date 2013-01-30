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

typedef boost::numeric::ublas::matrix<double> MatrixD;

class Cluster;

class View {
 public:
  //FIXME: add constructor with ranges as arguments, rather than recalculate
  View(const MatrixD data,
       std::vector<std::vector<int> > row_partitioning,
       std::vector<int> global_row_indices,
       std::vector<int> global_col_indices,
       std::map<int, std::map<std::string, double> > &hypers_m,
       std::vector<double> ROW_CRP_ALPHA_GRID,
       std::vector<double> R_GRID,
       std::vector<double> NU_GRID,
       std::map<int, std::vector<double> > S_GRIDS,
       std::map<int, std::vector<double> > MU_GRIDS,
       double CRP_ALPHA,
       int SEED=0);
  View(const MatrixD data,
       std::vector<int> global_row_indices,
       std::vector<int> global_col_indices,
       std::map<int, std::map<std::string, double> > &hypers_m,
       std::vector<double> ROW_CRP_ALPHA_GRID,
       std::vector<double> R_GRID,
       std::vector<double> NU_GRID,
       std::map<int, std::vector<double> > S_GRIDS,
       std::map<int, std::vector<double> > MU_GRIDS,
       int SEED=0);
  View(std::vector<int> global_row_indices,
       std::vector<double> ROW_CRP_ALPHA_GRID,
       std::vector<double> R_GRID,
       std::vector<double> NU_GRID,
       std::map<int, std::vector<double> > S_GRIDS,
       std::map<int, std::vector<double> > MU_GRIDS,
       int SEED=0);
  //
  // getters (external use)
  double get_num_vectors() const;
  double get_num_cols() const;
  int get_num_clusters() const;
  double get_crp_score() const;
  double get_data_score() const;
  double get_score() const;
  double get_crp_alpha() const;
  std::vector<double> get_crp_alpha_grid() const;
  std::vector<std::string> get_hyper_strings();
  std::vector<double> get_hyper_grid(int global_col_idx, std::string which_hyper);
  std::map<std::string, double> get_hypers(int local_col_idx) const;
  //
  // API helpers
  std::map<std::string, double> get_row_partition_model_hypers() const;
  std::vector<int> get_row_partition_model_counts() const;
  std::vector<std::map<std::string, double> > get_column_component_suffstats_i(int global_col_idx) const;
  std::vector<std::vector<std::map<std::string, double> > > get_column_component_suffstats() const;
  //
  // getters (internal use)
  Cluster& get_cluster(int cluster_idx);
  std::vector<int> get_cluster_counts() const;
  //
  // calculators
  double calc_cluster_vector_predictive_logp(std::vector<double> vd, Cluster cd,
					     double &crp_logp_delta,
					     double &data_logp_delta) const;
  std::vector<double> calc_cluster_vector_predictive_logps(std::vector<double> vd);
  double calc_crp_marginal() const;
  std::vector<double> calc_crp_marginals(std::vector<double> alphas) const;
  std::vector<double> calc_hyper_conditionals(int which_col,
					      std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  double calc_column_predictive_logp(std::vector<double> column_data,
				     std::vector<int> data_global_row_indices,
				     std::map<std::string, double> hypers);
  //
  // mutators
  void set_row_partitioning(std::vector<std::vector<int> > row_partitioning);
  void set_row_partitioning(std::vector<int> global_row_indices);
  double set_crp_alpha(double new_crp_alpha);
  Cluster& get_new_cluster();
  double insert_row(std::vector<double> vd, Cluster &cd, int row_idx);
  double insert_row(std::vector<double> vd, int row_idx);
  double remove_row(std::vector<double> vd, int row_idx); 
  double remove_col(int global_col_idx);
  double insert_col(std::vector<double> col_data,
		    std::vector<int> data_global_row_indices,
		    int global_col_idx,
		    std::map<std::string, double> &hypers);
  double insert_cols(const MatrixD data, 
		     std::vector<int> global_row_indices,
		     std::vector<int> global_col_indices,
		     std::map<int, std::map<std::string, double> > &hypers_m);
  void remove_if_empty(Cluster& which_cluster);
  void remove_all();
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
  std::vector<std::map<std::string, double>*> hypers_v;
  //
  // helper functions
  std::vector<double> align_data(std::vector<double> values,
				 std::vector<int> global_column_indices) const;
  std::vector<int> shuffle_row_indices();
  std::vector<std::vector<int> > get_cluster_groupings() const;
  std::vector<int> get_canonical_clustering() const;
  void print();
  void print_score_matrix();
  void assert_state_consistency();
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
  //
  // hyper inference grids FIXME: MOVE TO PRIVATE WHEN DONE TESTING
  std::map<int, int> global_to_local; // FIXME: specify appicability to columns
 private:
  // parameters
  double crp_alpha;
  double crp_score;
  double data_score;
  //  grids
  std::vector<double> crp_alpha_grid;
  std::vector<double> r_grid;
  std::vector<double> nu_grid;
  std::map<int, std::vector<double> > s_grids;
  std::map<int, std::vector<double> > mu_grids;
  // sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max);
  // helpers
  void construct_base_hyper_grids(int num_rows);
  void construct_column_hyper_grid(std::vector<double> col_data,
				   int gobal_col_idx);
  /* std::map<std::string, double> data_hypers; */
};

#endif //GUARD_view_h
