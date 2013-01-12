#include "Cluster.h"

using namespace std;

int Cluster::get_count() const {
  return count;
}

double Cluster::get_marginal_logp() const {
  return score;
}

ContinuousComponentModel Cluster::get_column_model(int idx) const {
  typename std::map<int, ContinuousComponentModel>::const_iterator it = \
    column_m.find(idx);
  if(it == column_m.end()) {
    // FIXME : how to fail properly?
    assert(1==0);
    ContinuousComponentModel ccm;
    return ccm;
  }
  return it->second;
}

std::set<int> Cluster::get_global_row_indices() const {
  return global_row_indices;
}

std::set<int> Cluster::get_global_col_indices() const {
  return global_col_indices;
}

std::map<int, double> Cluster::calc_marginal_logps() const {
  std::map<int, double> ret_map;
  typename std::map<int, ContinuousComponentModel>::const_iterator it = column_m.begin();
  for(; it!=column_m.end(); it++) {
    double logp = it->second.calc_marginal_logp();
    ret_map[it->first] = logp;
  }
  return ret_map;
}

double Cluster::calc_sum_marginal_logps() const {
  double sum_logp = 0;
  std::map<int, double> logp_map = calc_marginal_logps();
  typename std::map<int, double>::iterator it = logp_map.begin();
  for(; it!=logp_map.end(); it++) {
    sum_logp += it->second;
  }
  return sum_logp;
}

double Cluster::calc_predictive_logp(vector<double> vd) const {
  double sum_logps = 0;
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    double el = vd[col_idx];
    sum_logps += get_column_model(col_idx).calc_predictive_logp(el);
  }
  return sum_logps;
}

vector<double> Cluster::calc_hyper_conditionals(int which_col, string which_hyper, vector<double> hyper_grid) const {
  map<int, ContinuousComponentModel >::const_iterator it = column_m.find(which_col);
  ContinuousComponentModel sd = it->second;
  return sd.calc_hyper_conditionals(which_hyper, hyper_grid);
}

double Cluster::insert_row(vector<double> vd, int row_idx) {
  double sum_score_deltas = 0;
  count += 1;
  // track row indices
  pair<set<int>::iterator, bool> set_pair = \
    global_row_indices.insert(row_idx);
  assert(set_pair.second);
  // track score
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(column_m.count(col_idx)==1);
    sum_score_deltas += column_m[col_idx].insert(vd[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::remove_row(vector<double> vd, int row_idx) {
  double sum_score_deltas = 0;
  count -= 1;
  // track row indices
  int num_removed = global_row_indices.erase(row_idx);
  assert(num_removed!=0);
  // track score
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(column_m.count(col_idx)==1);
    sum_score_deltas += column_m[col_idx].remove(vd[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::set_hyper(int which_col, std::string which_hyper,
			  double hyper_value) {
  double score_delta = column_m[which_col].set_hyper(which_hyper, hyper_value);
  score += score_delta;
  return score_delta;
}

std::ostream& operator<<(std::ostream& os, const Cluster& c) {
  typename std::map<int, ContinuousComponentModel>::const_iterator it;
  for(it = c.column_m.begin(); it!= c.column_m.end(); it++) {
    os << "column idx: " << it->first << " :: ";
    os <<  c.global_row_indices << " :: " << it->second << std::endl;
  }
  os << "========" << std::endl;
  os << "cluster marginal logp: " << c.get_marginal_logp() << std::endl;
  return os;
}

void Cluster::init_columns() {
  count = 0;
  score = 0;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    column_m[col_idx] = ContinuousComponentModel();
    score += column_m[col_idx].calc_marginal_logp();
  }
}
