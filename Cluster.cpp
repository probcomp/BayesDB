#include "Cluster.h"

template <>
void Cluster<double>::init_suffstats() {
  count = 0;
  score = 0;
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    suffstats_m[col_idx] = Suffstats<double>();
    score += suffstats_m[col_idx].get_score();
  }
}

template <>
double Cluster<double>::insert_row(std::vector<double> vd, int row_idx) {
  double sum_score_deltas = 0;
  count += 1;
  // track row indices
  std::pair<std::set<int>::iterator, bool> set_pair = \
    global_row_indices.insert(row_idx);
  assert(set_pair.second);
  // track score
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(suffstats_m.count(col_idx)==1);
    sum_score_deltas += suffstats_m[col_idx].insert_el(vd[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

template <>
double Cluster<double>::remove_row(std::vector<double> vd, int row_idx) {
  double sum_score_deltas = 0;
  count -= 1;
  // track row indices
  int num_removed = global_row_indices.erase(row_idx);
  assert(num_removed!=0);
  // track score
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(suffstats_m.count(col_idx)==1);
    sum_score_deltas += suffstats_m[col_idx].remove_el(vd[col_idx]);
  }
  score += sum_score_deltas;
  return sum_score_deltas;
}

template <>
double Cluster<double>::calc_data_logp(std::vector<double> vd) const {
  double sum_logps = 0;
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    double el = vd[col_idx];
    const Suffstats<double> sd = get_suffstats_i(col_idx);
    sum_logps += sd.calc_data_logp(el);
  }
  return sum_logps;
}

template <>
double Cluster<double>::get_vector_logp(std::vector<double> vd) {
  // to be removed when test ensures calc_data_logps correctness
  double start_logp = calc_sum_logp();
  insert_row(vd, -1);
  double middle_logp = calc_sum_logp();
  remove_row(vd, -1);
  // double end_logp = calc_sum_logp();
  // assert(start_logp==end_logp);
  return middle_logp - start_logp;
}
