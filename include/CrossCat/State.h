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
	std::vector<std::string> GLOBAL_COL_DATATYPES,
	std::vector<int> GLOBAL_COL_MULTINOMIAL_COUNTS,
	std::vector<int> global_row_indices,
	std::vector<int> global_col_indices,
	std::map<int, std::map<std::string, double> > HYPERS_M,
	std::vector<std::vector<int> > column_partition,
	double COLUMN_CRP_ALPHA,
	std::vector<std::vector<std::vector<int> > > row_partition_v,
	std::vector<double> row_crp_alpha_v,
	int N_GRID=31, int SEED=0);
  State(const MatrixD &data,
	std::vector<std::string> GLOBAL_COL_DATATYPES,
	std::vector<int> GLOBAL_COL_MULTINOMIAL_COUNTS,
	std::vector<int> global_row_indices,
	std::vector<int> global_col_indices,
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
					   std::string col_datatype,
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
  std::map<int, std::string> global_col_datatypes;
  std::map<int, int> global_col_multinomial_counts;
  std::map<int, std::map<std::string, double> > hypers_m;
  double column_crp_alpha;
  double column_crp_score;
  double data_score;
  // grids
  std::vector<double> column_crp_alpha_grid;
  std::vector<double> row_crp_alpha_grid;
  std::vector<double> r_grid;
  std::vector<double> nu_grid;
  std::vector<double> multinomial_alpha_grid;
  std::map<int, std::vector<double> > s_grids;
  std::map<int, std::vector<double> > mu_grids;
  // lookups
  std::set<View*> views;
  std::map<int, View*> view_lookup;  // global_column_index to View mapping
  // sub-objects
  RandomNumberGenerator rng;
  // resources
  double draw_rand_u();
  int draw_rand_i(int max=MAX_INT);
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const State& s);
  std::string to_string(std::string join_str="\n") const;
  void construct_base_hyper_grids(int num_rows, int num_cols, int N_GRID);
  void construct_column_hyper_grids(boost::numeric::ublas::matrix<double> data,
				    std::vector<int> global_col_indices);
  std::map<std::string, double> get_default_hypers() const;
  void init_base_hypers();
  std::map<std::string, double> uniform_sample_hypers(int global_col_idx);
  void init_column_hypers(std::vector<int> global_col_indices);
  void init_views(const MatrixD &data,
		  std::map<int, std::string> global_col_datatypes,
		  std::vector<int> global_row_indices,
		  std::vector<int> global_col_indices,
		  std::vector<std::vector<int> > column_partition,
		  std::vector<std::vector<std::vector<int> > > row_partition_v,
		  std::vector<double> row_crp_alpha_v);
  void init_views(const MatrixD &data,
		  std::map<int, std::string> global_col_datatypes,
		  std::vector<int> global_row_indices,
		  std::vector<int> global_col_indices);
};

#endif // GUARD_state_h
