#ifndef GUARD_state_h
#define GUARD_state_h

#include <set>
#include <vector>
#include "View.h"
#include "utils.h"
#include "constants.h"
#include <fstream>
#include <iostream>
#include <algorithm>

#include <boost/numeric/ublas/io.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
typedef boost::numeric::ublas::matrix<double> MatrixD;

const static double r0_0 = 1.0;
const static double nu0_0 = 2.0;
const static double s0_0 = 2.0;
const static double mu0_0 = 0.0;

class State {
 public:
  State(const MatrixD &data,
	std::vector<int> global_row_indices,
	std::vector<int> global_col_indices,
	//std::vector<std::string> global_col_datatypes,
	int N_GRID=31, int SEED=0);
  ~State();
  //
  // getters
  int get_num_cols() const;
  int get_num_views() const;
  std::vector<int> get_view_counts() const;
  double get_column_crp_alpha() const;
  double get_column_crp_score() const;
  double get_data_score() const;
  double get_marginal_logp() const;
  std::map<int, std::set<int> > get_column_groups() const;
  // helpers for API
  std::map<std::string, double> get_row_partition_model_hypers_i(int view_idx) const;
  std::vector<int> get_row_partition_model_counts_i(int view_idx) const;
  std::vector<std::vector<std::map<std::string, double> > > get_column_component_suffstats_i(int view_idx) const;
  //
  std::vector<std::map<std::string, double> > get_column_hypers() const;
  std::map<std::string, double> get_column_partition_hypers() const;
  std::vector<int> get_column_partition_assignments() const;
  std::vector<int> get_column_partition_counts() const;
  std::vector<std::vector<int> > get_X_D() const;
  //
  // mutators
  double insert_feature(int feature_idx, std::vector<double> feature_data,
			View &which_view);
  double sample_insert_feature(int feature_idx, std::vector<double> feature_data,
			       View &singleton_view);
  double remove_feature(int feature_idx, std::vector<double> feature_data,
			View* &p_singleton_view);
  double transition_feature(int feature_idx, std::vector<double> feature_data);
  double transition_features(const MatrixD &data);
  View& get_new_view();
  View& get_view(int view_idx);
  void remove_if_empty(View& which_view);
  void remove_all();
  double transition_view_i(int which_view,
			 std::map<int, std::vector<double> > row_data_map);
  double transition_views(const MatrixD &data);
  double transition_column_crp_alpha();  
  double transition(const MatrixD &data);
  //
  // calculators
  double calc_feature_view_predictive_logp(std::vector<double> col_data,
					   View v,
					   double &crp_log_delta,
					   double &data_log_delta,
					   std::map<std::string, double> hypers) const;
					   
  std::vector<double> calc_feature_view_predictive_logps(std::vector<double> col_data, int global_col_idx) const;
  //
  // helpers
  double calc_column_crp_marginal() const;
  std::vector<double> calc_column_crp_marginals(std::vector<double> alphas_to_score) const;
  std::vector<double> calc_row_crp_marginals(std::vector<double> alphas_to_score) const;
  void SaveResult(std::string filename, int iter_idx=-1);
 private:
  // parameters
  std::map<int, std::map<std::string, double> > hypers_m;
  double column_crp_alpha;
  double column_crp_score;
  double data_score;
  std::vector<double> column_crp_alpha_grid;
  // lookups
  std::set<View*> views;
  std::map<int, View*> view_lookup;  // global_column_index to View mapping
  // sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max=MAX_INT);
  // helpers
  void construct_hyper_grids(boost::numeric::ublas::matrix<double> data,
			     int N_GRID);
  std::map<std::string, double> get_default_hypers() const;
  void init_hypers(std::vector<int> global_col_indices);
  void init_views(const MatrixD &data, std::vector<int> global_row_indices,
		  std::vector<int> global_col_indices);
};

#endif // GUARD_state_h
