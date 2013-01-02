#include "view.h"

static view NullView = view(0,0);

double view::get_score() const {
  return score;
}

double view::get_num_cols() const {
  return num_cols;
}

cluster<double>& view::get_new_cluster() {
  cluster<double> new_cluster = cluster<double>(num_cols);
  clusters.push_back(new_cluster);
  return clusters.back();
}

cluster<double>& view::get_cluster(int cluster_idx) {
  assert(cluster_idx <= clusters.size());
  bool not_new = cluster_idx < clusters.size();
  if(not_new) {
    return clusters[cluster_idx];
  } else {
    return get_new_cluster();
  }
}

cluster<double> view::copy_cluster(int cluster_idx) const {
  assert(cluster_idx <= clusters.size());
  bool not_new = cluster_idx < clusters.size();
  if(not_new) {
    return clusters[cluster_idx];
  } else {
    return cluster<double>(num_cols);
  }
}

double view::calc_cluster_vector_logp(std::vector<double> vd, int cluster_idx) const {
  cluster<double> which_cluster = copy_cluster(cluster_idx);
  int cluster_count = which_cluster.get_count();
  double crp_logp_delta, data_logp_delta, score_delta;
  crp_logp_delta = numerics::calc_cluster_crp_logp(cluster_count, num_vectors,
						   crp_alpha);
  data_logp_delta = which_cluster.calc_data_logp(vd);
  score_delta = crp_logp_delta + data_logp_delta;
  return score_delta;
}

std::vector<double> view::calc_cluster_vector_logps(std::vector<double> vd) const {
  std::vector<double> logps;
  std::cout << "clusters.size(): " << clusters.size() << std::endl;
  for(int cluster_idx=0; cluster_idx<clusters.size(); cluster_idx++) {
    logps.push_back(calc_cluster_vector_logp(vd, cluster_idx));
  }
  logps.push_back(calc_cluster_vector_logp(vd, clusters.size()));
  return logps;
}

double view::insert_row(std::vector<double> vd, int cluster_idx, int row_idx) {
  cluster<double>& which_cluster = get_cluster(cluster_idx);
  double score_delta = calc_cluster_vector_logp(vd, cluster_idx);
  which_cluster.insert_row(vd, row_idx);
  score += score_delta;
  return score_delta;
}

double view::remove_row(std::vector<double> vd, int cluster_idx, int row_idx) {
  cluster<double>& which_cluster = get_cluster(cluster_idx);
  which_cluster.remove_row(vd, row_idx);
  double score_delta = calc_cluster_vector_logp(vd, cluster_idx);
  score -= score_delta;
  return score_delta;
}

std::vector<int> view::get_cluster_counts() {
  std::vector<int> counts;
  std::vector<cluster<double> >::iterator it;
  for(; it!=clusters.end(); it++) {
    int count = (*it).get_global_row_indices().size();
    counts.push_back(count);
  }
  return counts;
}

double view::get_crp_score() {
  std::vector<int> cluster_counts = get_cluster_counts();
  return numerics::calc_crp_alpha_conditional(cluster_counts, crp_alpha, -1, true);
}

double view::get_data_score() {
  double data_score = 0;
  std::vector<cluster<double> >::iterator it;
  for(; it!=clusters.end(); it++) {
    double cluster_score = (*it).calc_sum_logp();
    data_score += cluster_score;
  }
  return data_score;
}
