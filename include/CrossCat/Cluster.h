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
#include "ContinuousComponentModel.h"


class Cluster {
 public:
  Cluster(int num_cols=0);
  //
  // getters
  int get_num_cols() const;
  int get_count() const;
  double get_marginal_logp() const;
  ContinuousComponentModel get_model(int idx) const;
  std::set<int> get_row_indices() const;
  //
  // calculators
  std::vector<double> calc_marginal_logps() const;
  double calc_sum_marginal_logps() const ;
  double calc_predictive_logp(std::vector<double> vd) const;
  std::vector<double> calc_hyper_conditionals(int which_col,
					      std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  //
  // mutators
  double insert_row(std::vector<double> values, int row_idx);
  double remove_row(std::vector<double> values, int row_idx);
  double remove_col(int col_idx);
  double insert_col(std::vector<double> data,
		    std::vector<int> data_global_row_indices);
  double set_hyper(int which_col, std::string which_hyper, double hyper_value);
  //
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const Cluster& c);
 private:
  int count;
  double score;
  void init_columns(int num_cols);
  std::vector<ContinuousComponentModel> model_v;
  std::set<int> row_indices;
};

#endif // GUARD_cluster_h
