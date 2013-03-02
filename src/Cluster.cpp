#include "Cluster.h"

using namespace std;

Cluster::Cluster(vector<map<string, double>*> &hypers_v) {
  init_columns(hypers_v);
}

// Cluster::Cluster(const vector<map<string, double>*> &hypers_v) {
//   vector<map<string, double>*> temp_hypers_v = hypers_v;
//   init_columns(temp_hypers_v);
// }

Cluster::Cluster() {
  vector<map<string, double>*> hypers_v;
  init_columns(hypers_v);
}

int Cluster::get_num_cols() const {
  return p_model_v.size();
}

int Cluster::get_count() const {
  return row_indices.size();
}

double Cluster::get_marginal_logp() const {
  return score;
}

map<string, double> Cluster::get_suffstats_i(int idx) const {
  return p_model_v[idx]->get_suffstats();
}

map<string, double> Cluster::get_hypers_i(int idx) const {
  return p_model_v[idx]->get_hypers();
}

set<int> Cluster::get_row_indices_set() const {
  return row_indices;
}

vector<int> Cluster::get_row_indices_vector() const {
  return set_to_vector(row_indices);
}

std::vector<double> Cluster::calc_marginal_logps() const {
  std::vector<double> logps;
  typename std::vector<ComponentModel*>::const_iterator it;
  for(it=p_model_v.begin(); it!=p_model_v.end(); it++) {
    double logp = (**it).calc_marginal_logp();
    logps.push_back(logp);
  }
  return logps;
}

double Cluster::calc_sum_marginal_logps() const {
  std::vector<double> logp_map = calc_marginal_logps();
  double sum_logps = std::accumulate(logp_map.begin(), logp_map.end(), 0.);
  return sum_logps;
}

double Cluster::calc_row_predictive_logp(vector<double> values) const {
  double sum_logps = 0;
  for(unsigned int col_idx=0; col_idx<values.size(); col_idx++) {
    double el = values[col_idx];
    sum_logps += p_model_v[col_idx]->calc_element_predictive_logp(el);
  }
  return sum_logps;
}

vector<double> Cluster::calc_hyper_conditionals(int which_col,
						string which_hyper,
						vector<double> hyper_grid) const {
  ComponentModel *ccm = p_model_v[which_col];
  vector<double> hyper_conditionals = ccm->calc_hyper_conditionals(which_hyper,
								  hyper_grid);
  return hyper_conditionals;
}

double Cluster::calc_column_predictive_logp(vector<double> column_data,
					    string col_datatype,
					    vector<int> data_global_row_indices,
					    map<string, double> hypers) {
  map<int, int> global_to_data = construct_lookup_map(data_global_row_indices);
  ComponentModel *p_cm;
  if(col_datatype==CONTINUOUS_DATATYPE) {
    p_cm = new ContinuousComponentModel(hypers);
  } else if(col_datatype==CONTINUOUS_DATATYPE) {
    p_cm = new MultinomialComponentModel(hypers);
  } else {
    assert(1==0);
  }
  set<int>::iterator it;
  for(it=row_indices.begin(); it!=row_indices.end(); it++) {
    int global_row_idx = *it;
    int data_idx = global_to_data[global_row_idx];
    double value = column_data[data_idx];
    p_cm->insert_element(value);
  }
  double score_delta = p_cm->calc_marginal_logp();
  delete p_cm;
  return score_delta;
}

double Cluster::insert_row(vector<double> values, int row_idx) {
  double sum_score_deltas = 0;
  // track row indices
  pair<set<int>::iterator, bool> set_pair = \
    row_indices.insert(row_idx);
  assert(set_pair.second);
  // track score
  for(unsigned int col_idx=0; col_idx<values.size(); col_idx++) {
    sum_score_deltas += p_model_v[col_idx]->insert_element(values[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::remove_row(vector<double> values, int row_idx) {
  double sum_score_deltas = 0;
  // track row indices
  unsigned int num_removed = row_indices.erase(row_idx);
  assert(num_removed!=0);
  // track score
  for(unsigned int col_idx=0; col_idx<values.size(); col_idx++) {
    sum_score_deltas += p_model_v[col_idx]->remove_element(values[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

double Cluster::remove_col(int col_idx) {
  double score_delta = p_model_v[col_idx]->calc_marginal_logp();
  // FIXME: make sure destruction proper
  ComponentModel *p_cm = p_model_v[col_idx];
  p_model_v.erase(p_model_v.begin() + col_idx);
  delete p_cm;
  score -= score_delta;
  return score_delta;
}

double Cluster::insert_col(vector<double> data,
			   string col_datatype,
			   vector<int> data_global_row_indices,
			   map<string, double> &hypers) {
  map<int, int> global_to_data = construct_lookup_map(data_global_row_indices);
  ComponentModel *p_cm;
  if(col_datatype==CONTINUOUS_DATATYPE) {
    p_cm = new ContinuousComponentModel(hypers);
  } else if(col_datatype==CONTINUOUS_DATATYPE) {
    p_cm = new MultinomialComponentModel(hypers);
  } else {
    assert(1==0);
  }
  set<int>::iterator it;
  for(it=row_indices.begin(); it!=row_indices.end(); it++) {
    int global_row_idx = *it;
    int data_idx = global_to_data[global_row_idx];
    double value = data[data_idx];
    p_cm->insert_element(value);
  }
  double score_delta = p_cm->calc_marginal_logp();
  p_model_v.push_back(p_cm);
  score += score_delta;
  //
  return score_delta;
}

double Cluster::incorporate_hyper_update(int which_col) {
  double score_delta = p_model_v[which_col]->incorporate_hyper_update();
  score += score_delta;
  return score_delta;
}


std::ostream& operator<<(std::ostream& os, const Cluster& c) {
  os << "========" << std::endl;
  os <<  "cluster row_indices:: " << c.row_indices << endl;
  for(int col_idx=0; col_idx<c.get_num_cols(); col_idx++) {
    os << endl << "column idx: " << col_idx << " :: " << *(c.p_model_v[col_idx]);
  }
  os << "========" << std::endl;
  os << "cluster marginal logp: " << c.get_marginal_logp() << std::endl;
  return os;
}

void Cluster::init_columns(vector<map<string, double>*> &hypers_v) {
  score = 0;
  vector<map<string, double>*>::iterator it;
  for(it=hypers_v.begin(); it!=hypers_v.end(); it++) {
    map<string, double> &hypers = **it;
    string continuous_key = "nu";
    string multinomial_key = "multinomial_alpha";
    if(in(hypers, continuous_key)) {
      // FIXME: should be passed col_datatypes here
      //         and instantiate correct type?
      ComponentModel *p_cm = new ContinuousComponentModel(hypers);
      p_model_v.push_back(p_cm);
    } else if(in(hypers, multinomial_key)) {
      ComponentModel *p_cm = new MultinomialComponentModel(hypers);
      p_model_v.push_back(p_cm);
    } else {
      assert(1==0);
    }
    int col_idx = p_model_v.size() - 1;
    score += p_model_v[col_idx]->calc_marginal_logp();
  }
}
