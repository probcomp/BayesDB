#include "Cluster.h"

using namespace std;

Cluster::Cluster(int num_cols) {
  init_columns(num_cols);
}

int Cluster::get_num_cols() const {
  return model_v.size();
}

int Cluster::get_count() const {
  return row_indices.size();
}

double Cluster::get_marginal_logp() const {
  return score;
}

ContinuousComponentModel Cluster::get_model(int idx) const {
  return model_v[idx];
}

set<int> Cluster::get_row_indices() const {
  return row_indices;
}

std::vector<double> Cluster::calc_marginal_logps() const {
  std::vector<double> logps;
  typename std::vector<ContinuousComponentModel>::const_iterator it;
  for(it=model_v.begin(); it!=model_v.end(); it++) {
    double logp = (*it).calc_marginal_logp();
    logps.push_back(logp);
  }
  return logps;
}

double Cluster::calc_sum_marginal_logps() const {
  std::vector<double> logp_map = calc_marginal_logps();
  double sum_logps = std::accumulate(logp_map.begin(), logp_map.end(), 0.);
  return sum_logps;
}

double Cluster::calc_predictive_logp(vector<double> values) const {
  double sum_logps = 0;
  for(int col_idx=0; col_idx<values.size(); col_idx++) {
    double el = values[col_idx];
    sum_logps += get_model(col_idx).calc_predictive_logp(el);
  }
  return sum_logps;
}

vector<double> Cluster::calc_hyper_conditionals(int which_col,
						string which_hyper,
						vector<double> hyper_grid) const {
  ContinuousComponentModel ccm = model_v[which_col];
  vector<double> hyper_conditionals = ccm.calc_hyper_conditionals(which_hyper,
								  hyper_grid);
  return hyper_conditionals;
}

double Cluster::insert_row(vector<double> values, int row_idx) {
  double sum_score_deltas = 0;
  // track row indices
  pair<set<int>::iterator, bool> set_pair = \
    row_indices.insert(row_idx);
  assert(set_pair.second);
  // track score
  for(int col_idx=0; col_idx<values.size(); col_idx++) {
    sum_score_deltas += model_v[col_idx].insert(values[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::remove_row(vector<double> values, int row_idx) {
  double sum_score_deltas = 0;
  // track row indices
  int num_removed = row_indices.erase(row_idx);
  assert(num_removed!=0);
  // track score
  for(int col_idx=0; col_idx<values.size(); col_idx++) {
    sum_score_deltas += model_v[col_idx].remove(values[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::remove_col(int col_idx) {
  double score_delta = model_v[col_idx].calc_marginal_logp();
  model_v.erase(model_v.begin() + col_idx);
  score -= score_delta;
  return score_delta;
}

double Cluster::insert_col(vector<double> data,
			   vector<int> data_global_row_indices) {
  map<int, int> global_to_data = construct_lookup_map(data_global_row_indices);
  ContinuousComponentModel ccm;
  set<int>::iterator it;
  for(it=row_indices.begin(); it!=row_indices.end(); it++) {
    int global_row_idx = *it;
    int data_idx = global_to_data[global_row_idx];
    double value = data[data_idx];
    ccm.insert(value);
  }
  double score_delta = ccm.calc_marginal_logp();
  model_v.push_back(ccm);
  score += score_delta;
  //
  cout << "insert_col:: score_delta: " << score_delta << endl;
  int col_idx = model_v.size() - 1;
  cout << "insert_col:: score_delta: " << model_v[col_idx].calc_marginal_logp() << endl;
  return score_delta;
}

double Cluster::set_hyper(int which_col, std::string which_hyper,
			  double hyper_value) {
  double score_delta = model_v[which_col].set_hyper(which_hyper, hyper_value);
  score += score_delta;
  return score_delta;
}

std::ostream& operator<<(std::ostream& os, const Cluster& c) {
  os << "========" << std::endl;
  os <<  "cluster row_indices:: " << c.row_indices << endl;
  for(int col_idx=0; col_idx<c.get_num_cols(); col_idx++) {
    os << endl << "column idx: " << col_idx << " :: " << c.model_v[col_idx];
  }
  os << "========" << std::endl;
  os << "cluster marginal logp: " << c.get_marginal_logp() << std::endl;
  return os;
}

void Cluster::init_columns(int num_cols) {
  score = 0;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    model_v.push_back(ContinuousComponentModel());
    score += model_v[col_idx].calc_marginal_logp();
  }
}
