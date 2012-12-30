#include "cluster.h"

template <>
void cluster<double>::init_suffstats() {
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    suffstats_m[col_idx] = suffstats<double>();
  }
}

template <>
void cluster<double>::insert_row(std::vector<double> vd, int row_idx) {
  std::pair<std::set<int>::iterator, bool> set_pair = \
    global_row_indices.insert(row_idx);
  assert(set_pair.second);
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(suffstats_m.count(col_idx)==1);
    suffstats_m[col_idx].insert_el(vd[col_idx]);
  }
}

template <>
void cluster<double>::remove_row(std::vector<double> vd, int row_idx) {
  int num_removed = global_row_indices.erase(row_idx);
  assert(num_removed!=0);
  for(int col_idx=0; col_idx<vd.size(); col_idx++) {
    assert(suffstats_m.count(col_idx)==1);
    suffstats_m[col_idx].remove_el(vd[col_idx]);
  }
}

template <>
double cluster<double>::get_vector_logp(std::vector<double> vd) {
  double start_logp = calc_sum_logp();
  insert_row(vd, -1);
  double middle_logp = calc_sum_logp();
  remove_row(vd, -1);
  // double end_logp = calc_sum_logp();
  // assert(start_logp==end_logp);
  return middle_logp - start_logp;
}
