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
  //Cluster(const std::vector<std::map<std::string, double>*> hypers_v);
  Cluster(std::vector<std::map<std::string, double>*> &hypers_v);
  Cluster();
  //
  // getters
  int get_num_cols() const;
  int get_count() const;
  double get_marginal_logp() const;
  ContinuousComponentModel get_model(int idx) const;
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
				     std::vector<int> data_global_row_indices,
				     std::map<std::string, double> hypers);
  //
  // mutators
  double insert_row(std::vector<double> values, int row_idx);
  double remove_row(std::vector<double> values, int row_idx);
  double remove_col(int col_idx);
  double insert_col(std::vector<double> data,
		    std::vector<int> data_global_row_indices,
		    std::map<std::string, double> &hypers);
  double incorporate_hyper_update(int which_col);
  //
  // helpers
  friend std::ostream& operator<<(std::ostream& os, const Cluster& c);
  //
  // make private later
  std::vector<ContinuousComponentModel> model_v;
 private:
  int count;
  double score;
  void init_columns(std::vector<std::map<std::string, double>*> &hypers_v);
  std::set<int> row_indices;
};

#endif // GUARD_cluster_h
