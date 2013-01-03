#include "View.h"

static View NullView = View(0,0);
static Cluster<double> NullCluster = Cluster<double>(0);

void View::print() {
  std::cout << clusters << std::endl;
}

double View::get_score() const {
  return score;
}

double View::get_num_vectors() const {
  return num_vectors;
}

double View::get_num_cols() const {
  return num_cols;
}

// Cluster<double>& View::get_cluster_location(int row_idx) {
//   std::map<int, Cluster<double>*>::iterator it = \
//     cluster_lookup.find(row_idx);
//   bool in_map = it!=cluster_lookup.end();
//   if(in_map) return *(it->second);
//   return NullCluster;
// }

// int View::get_cluster_location_idx(int row_idx) {
//   Cluster<double>& cd = get_cluster_location(row_idx);
//   std::cout << cd << std::endl;
//   int i;
//   for(i=0; i<clusters.size(); i++) {
//     if(clusters[i]==&cd) break;
//   }
//   return i;
// }

Cluster<double>& View::get_new_cluster() {
  Cluster<double> *p_new_cluster = new Cluster<double>(num_cols);
  clusters.insert(p_new_cluster);
  return *p_new_cluster;
}

Cluster<double>& View::get_cluster(int cluster_idx) {
  assert(cluster_idx <= clusters.size());
  bool not_new = cluster_idx < clusters.size();
  if(not_new) {
    std::set<Cluster<double>*>::iterator it = clusters.begin();
    for(int i=0; i<cluster_idx; i++) {it++;}
    return **it;
  } else {
    return get_new_cluster();
  }
}

// Cluster<double> View::copy_cluster(int cluster_idx) const {
//   assert(cluster_idx <= clusters.size());
//   bool not_new = cluster_idx < clusters.size();
//   return not_new ? clusters[cluster_idx] : Cluster<double>(num_cols);
// }

double View::calc_cluster_vector_logp(std::vector<double> vd, Cluster<double> which_cluster) const {
  int cluster_count = which_cluster.get_count();
  double crp_logp_delta, data_logp_delta, score_delta;
  // NOTE: non-mutating, so presume vector is not in state
  // so use num_vectors, not num_vectors - 1
  // should try to cache counts in some way
  crp_logp_delta = numerics::calc_cluster_crp_logp(cluster_count,
						   num_vectors,
						   crp_alpha);
  data_logp_delta = which_cluster.calc_data_logp(vd);
  score_delta = crp_logp_delta + data_logp_delta;
  return score_delta;
}

std::vector<double> View::calc_cluster_vector_logps(std::vector<double> vd) const {
  std::vector<double> logps;
  for(int cluster_idx=0; cluster_idx<clusters.size(); cluster_idx++) {
    logps.push_back(calc_cluster_vector_logp(vd, cluster_idx));
  }
  logps.push_back(calc_cluster_vector_logp(vd, clusters.size()));
  return logps;
}

double View::insert_row(std::vector<double> vd, Cluster<double>& which_cluster, int row_idx) {
  double score_delta = calc_cluster_vector_logp(vd, which_cluster);
  which_cluster.insert_row(vd, row_idx);
  cluster_lookup[row_idx] = &which_cluster;
  score += score_delta;
  num_vectors += 1;
  return score_delta;
}

void View::remove_if_empty(Cluster<double>& which_cluster) {
  if(which_cluster.get_count()==0) {
    clusters.erase(clusters.find(&which_cluster));
    delete &which_cluster;
  }
}

double View::remove_row(std::vector<double> vd, Cluster<double>& which_cluster, int row_idx) {
  cluster_lookup.erase(cluster_lookup.find(row_idx));
  which_cluster.remove_row(vd, row_idx);
  num_vectors -= 1;
  double score_delta = calc_cluster_vector_logp(vd, which_cluster);
  remove_if_empty(which_cluster);
  score -= score_delta;
  return score_delta;
}

std::vector<int> View::get_cluster_counts() const {
  std::vector<int> counts;
  std::set<Cluster<double>*>::const_iterator it = clusters.begin();
  for(; it!=clusters.end(); it++) {
    int count = (**it).get_count();
    counts.push_back(count);
  }
  return counts;
}

double View::get_crp_score() const {
  std::vector<int> cluster_counts = get_cluster_counts();
  std::cout << "cluster_counts: " << cluster_counts << std::endl;
  return numerics::calc_crp_alpha_conditional(cluster_counts, crp_alpha, -1, true);
}

// double View::get_data_score() {
//   double data_score = 0;
//   std::set<Cluster<double>*>::iterator it = clusters.begin()
//   for(; it!=clusters.end(); it++) {
//     double cluster_score = (**it).calc_sum_logp();
//     data_score += cluster_score;
//   }
//   return data_score;
// }
