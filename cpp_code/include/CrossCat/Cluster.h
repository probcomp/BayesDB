#ifndef GUARD_cluster_h
#define GUARD_cluster_h

// #include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <set>
#include <stdio.h>
#include "assert.h"
//
#include "utils.h"
#include "constants.h"
#include "ComponentModel.h"
#include "ContinuousComponentModel.h"
#include "MultinomialComponentModel.h"


class Cluster {
 public:
  //Cluster(const std::vector<CM_Hypers*> hypers_v);
  Cluster(std::vector<CM_Hypers*> &hypers_v);
  Cluster();
  //
  // getters
  int get_num_cols() const;
  int get_count() const;
  double get_marginal_logp() const;
  std::map<std::string, double> get_suffstats_i(int idx) const;
  CM_Hypers get_hypers_i(int idx) const;
  std::set<int> get_row_indices_set() const;
  std::vector<int> get_row_indices_vector() const;
  //
  // calculators
  std::vector<double> calc_marginal_logps() const;
  double calc_sum_marginal_logps() const ;
  double calc_row_predictive_logp(std::vector<double> vd) const;
  std::vector<double> calc_hyper_conditionals(int which_col,
					      std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  double calc_column_predictive_logp(std::vector<double> column_data,
				     std::string col_datatype,
				     std::vector<int> data_global_row_indices,
				     CM_Hypers hypers);
  //
  // mutators
  double insert_row(std::vector<double> values, int row_idx);
  double remove_row(std::vector<double> values, int row_idx);
  double remove_col(int col_idx);
  double insert_col(std::vector<double> data,
		    std::string col_datatype,
		    std::vector<int> data_global_row_indices,
		    CM_Hypers &hypers);
  double incorporate_hyper_update(int which_col);
  void delete_component_models(bool check_empty=true);
  //
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const Cluster& c);
  std::string to_string(std::string join_str="\n", bool top_level=false) const;
  //
  // make private later
  std::vector<ComponentModel*> p_model_v;
 private:
  double score;
  void init_columns(std::vector<CM_Hypers*> &hypers_v);
  std::set<int> row_indices;
};

#endif // GUARD_cluster_h
