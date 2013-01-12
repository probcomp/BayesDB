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
  Cluster(): num_cols(5) { init_columns(); };
  Cluster(int NUM_COLS): num_cols(NUM_COLS) { init_columns(); };
  //
  // getters
  int get_count() const;
  double get_marginal_logp() const;
  ContinuousComponentModel get_column_model(int idx) const;
  std::set<int> get_global_row_indices() const;
  std::set<int> get_global_col_indices() const;
  //
  // calculators
  std::map<int, double> calc_marginal_logps() const;
  double calc_sum_marginal_logps() const ;
  double calc_predictive_logp(std::vector<double> vd) const;
  std::vector<double> calc_hyper_conditionals(int which_col,
					      std::string which_hyper,
					      std::vector<double> hyper_grid) const;
  //
  // mutators
  double insert_row(std::vector<double> vd, int row_idx);
  double remove_row(std::vector<double> vd, int row_idx);
  double set_hyper(int which_col, std::string which_hyper, double hyper_value);
  //
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const Cluster& c);
 private:
  int num_cols;
  int count;
  double score;
  void init_columns();
  std::map<int, ContinuousComponentModel> column_m;
  std::set<int> global_row_indices;
  std::set<int> global_col_indices;
};

#endif // GUARD_cluster_h
