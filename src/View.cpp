#include "View.h"

using namespace std;

static View NullView = View(0,0);
static Cluster<double> NullCluster = Cluster<double>(0);

View::View(int NUM_COLS, double CRP_ALPHA) {
  num_vectors = 0;
  num_cols = NUM_COLS;
  crp_alpha = CRP_ALPHA;
  crp_score = 0;
  data_score = 0;
}

double View::get_num_vectors() const {
  return num_vectors;
}

double View::get_num_cols() const {
  return num_cols;
}

int View::get_num_clusters() const {
  return clusters.size();
}

double View::get_crp_alpha() const {
  return crp_alpha;
}

double View::get_crp_score() const {
  return crp_score;
}

double View::get_data_score() const {
  return data_score;
}

double View::get_score() const {
  return crp_score + data_score;
}

Cluster<double>& View::get_cluster(int cluster_idx) {
  assert(cluster_idx <= clusters.size());
  bool not_new = cluster_idx < clusters.size();
  if(not_new) {
    set<Cluster<double>*>::iterator it = clusters.begin();
    std::advance(it, cluster_idx);
    return **it;
  } else {
    return get_new_cluster();
  }
}

vector<int> View::get_cluster_counts() const {
  vector<int> counts;
  set<Cluster<double>*>::const_iterator it = clusters.begin();
  for(; it!=clusters.end(); it++) {
    int count = (**it).get_count();
    counts.push_back(count);
  }
  return counts;
}

double View::calc_cluster_vector_logp(vector<double> vd, Cluster<double> which_cluster, double &crp_logp_delta, double &data_logp_delta) const {
  int cluster_count = which_cluster.get_count();
  double score_delta;
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

vector<double> View::calc_cluster_vector_logps(vector<double> vd) const {
  vector<double> logps;
  set<Cluster<double>*>::iterator it = clusters.begin();
  double crp_logp_delta, data_logp_delta;
  for(; it!=clusters.end(); it++) {
    logps.push_back(calc_cluster_vector_logp(vd, **it, crp_logp_delta, data_logp_delta));
  }
  Cluster<double> empty_cluster(num_cols);
  logps.push_back(calc_cluster_vector_logp(vd, empty_cluster, crp_logp_delta, data_logp_delta));
  return logps;
}

double View::score_crp() const {
  vector<int> cluster_counts = get_cluster_counts();
  return numerics::calc_crp_alpha_conditional(cluster_counts, crp_alpha, -1, true);
}

vector<double> View::score_crp(vector<double> alphas_to_score) const {
  vector<int> cluster_counts = get_cluster_counts();
  vector<double> crp_scores;
  vector<double>::iterator it = alphas_to_score.begin();
  for(; it!=alphas_to_score.end(); it++) {
    double alpha_to_score = *it;
    double this_crp_score = numerics::calc_crp_alpha_conditional(cluster_counts, alpha_to_score, -1, true);
    crp_scores.push_back(this_crp_score);
  }
  return crp_scores;
}

double View::set_alpha(double new_alpha) {
  double crp_score_0 = crp_score;
  crp_alpha = new_alpha;
  crp_score = score_crp();
  return crp_score - crp_score_0;
}

Cluster<double>& View::get_new_cluster() {
  Cluster<double> *p_new_cluster = new Cluster<double>(num_cols);
  clusters.insert(p_new_cluster);
  return *p_new_cluster;
}

double View::insert_row(vector<double> vd, Cluster<double>& which_cluster, int row_idx) {
  // NOTE: MUST use calc_cluster_vector_logp,  gets crp_score_delta as well
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_cluster_vector_logp(vd, which_cluster, crp_logp_delta, data_logp_delta);
  which_cluster.insert_row(vd, row_idx);
  cluster_lookup[row_idx] = &which_cluster;
  crp_score += crp_logp_delta;
  data_score += data_logp_delta;
  num_vectors += 1;
  return score_delta;
}

double View::remove_row(vector<double> vd, int row_idx) {
  Cluster<double> &which_cluster = *(cluster_lookup[row_idx]);
  cluster_lookup.erase(cluster_lookup.find(row_idx));
  which_cluster.remove_row(vd, row_idx);
  num_vectors -= 1;
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_cluster_vector_logp(vd, which_cluster, crp_logp_delta, data_logp_delta);
  remove_if_empty(which_cluster);
  crp_score -= crp_logp_delta;
  data_score -= data_logp_delta;
  return score_delta;
}

void View::remove_if_empty(Cluster<double>& which_cluster) {
  if(which_cluster.get_count()==0) {
    clusters.erase(clusters.find(&which_cluster));
    delete &which_cluster;
  }
}

void View::transition_z(vector<double> vd, int row_idx) {
  remove_row(vd, row_idx);
  vector<double> unorm_logps = calc_cluster_vector_logps(vd);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  Cluster<double> &which_cluster = get_cluster(draw);
  insert_row(vd, which_cluster, row_idx);
}

void View::transition_zs(map<int, vector<double> > row_data_map) {
  vector<int> shuffled_row_indices = shuffle_row_indices();
  vector<int>::iterator it = shuffled_row_indices.begin();
  for(; it!=shuffled_row_indices.end(); it++) {
    int row_idx = *it;
    vector<double> vd = row_data_map[row_idx];
    transition_z(vd, row_idx);
  }
}

vector<int> View::shuffle_row_indices() {
  // can't use std::random_shuffle b/c need to control seed
  vector<int> original_order;
  map<int, Cluster<double>*>::iterator it = cluster_lookup.begin();
  for(; it!=cluster_lookup.end(); it++) {
    original_order.push_back(it->first);
  }
  vector<int> shuffled_order;
  while(original_order.size()!=0) {
    int draw = draw_rand_i(original_order.size());
    int row_idx = original_order[draw];
    shuffled_order.push_back(row_idx);
    original_order.erase(original_order.begin() + draw);
  }
  return shuffled_order;
}

void View::print() {
  set<Cluster<double>*>::iterator it = clusters.begin();
  for(; it!=clusters.end(); it++) {
    cout << **it << endl;
  }
  cout << "crp_score: " << crp_score << ", " << "data_score: " << data_score << ", " << "score: " << get_score() << endl;
}

void View::assert_state_consistency() {
  double tolerance = 1E-10;
  vector<int> cluster_counts = get_cluster_counts();
  assert(is_almost(get_num_vectors(), std::accumulate(cluster_counts.begin(),cluster_counts.end(),0),tolerance));
  assert(is_almost(get_crp_score(),score_crp(),tolerance));
}

double View::draw_rand_u() {
  return rng.next();
}

int View::draw_rand_i(int max) {
  return rng.nexti(max);
}
