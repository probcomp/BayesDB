#include "View.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
#include <boost/numeric/ublas/io.hpp>
typedef boost::numeric::ublas::matrix<double> MatrixD;

using namespace std;

typedef set<Cluster*> setCp;

//FIXME: add constructor with ranges as arguments, rather than recalculate
View::View(MatrixD data, int N_GRID) {
  int data_num_vectors = data.size1();
  num_cols = data.size2();
  vector<double> paramRange = linspace(0.03, .97, N_GRID/2);
  int APPEND_N = (N_GRID + 1) / 2;
  //
  vector<double> crp_alpha_grid_append = log_linspace(1., data_num_vectors,
						      APPEND_N);
  crp_alpha_grid = append(paramRange, crp_alpha_grid_append);
  //
  r_grid = crp_alpha_grid;
  //
  vector<double> nu_grid_append = log_linspace(1., data_num_vectors/2.,
					       APPEND_N);
  nu_grid = append(paramRange, nu_grid_append);
  //
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    vector<double> col_data = extract_col(data, col_idx);
    double sum_sq_deviation = calc_sum_sq_deviation(col_data);
    vector<double> s_grid_append = log_linspace(1., sum_sq_deviation, APPEND_N);
    vector<double> s_grid = append(paramRange, s_grid_append);
    s_grids.push_back(s_grid);
  }
  //
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    vector<double> col_data = extract_col(data, col_idx);
    double min = *std::min_element(col_data.begin(), col_data.end());
    double max = *std::max_element(col_data.begin(), col_data.end());
    vector<double> mu_grid_append = linspace(min, max, APPEND_N);
    vector<double> mu_grid = append(paramRange, mu_grid_append);
    mu_grids.push_back(mu_grid);
  }
  //
  crp_alpha = 3;
  //
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

double View::get_crp_score() const {
  return crp_score;
}

double View::get_data_score() const {
  return data_score;
}

double View::get_score() const {
  return crp_score + data_score;
}

double View::get_crp_alpha() const {
  return crp_alpha;
}

vector<string> View::get_hyper_strings() {
  vector<string> hyper_strings;
  hyper_strings.push_back("r");
  hyper_strings.push_back("nu");
  hyper_strings.push_back("s");
  hyper_strings.push_back("mu");
  return hyper_strings;
}

std::map<string, double> View::get_hypers(int col_idx) {
  // assume all suffstats have same hypers set
  setCp::iterator it = clusters.begin();
  map<string, double> ret_map = (**it).get_column_model(col_idx).get_hypers();
  return ret_map;
}

vector<double> View::get_hyper_grid(int which_col, std::string which_hyper) {
  vector<double> hyper_grid;
  if(which_hyper=="r") {
    hyper_grid = r_grid;
  } else if (which_hyper=="nu") {
    hyper_grid = nu_grid;
  } else if (which_hyper=="s") {
    hyper_grid = s_grids[which_col];
  } else if (which_hyper=="mu") {
    hyper_grid = mu_grids[which_col];
  }
  return hyper_grid;
}

Cluster& View::get_cluster(int cluster_idx) {
  assert(cluster_idx <= clusters.size());
  bool not_new = cluster_idx < clusters.size();
  if(not_new) {
    set<Cluster*>::iterator it = clusters.begin();
    std::advance(it, cluster_idx);
    return **it;
  } else {
    return get_new_cluster();
  }
}

vector<int> View::get_cluster_counts() const {
  vector<int> counts;
  set<Cluster*>::const_iterator it = clusters.begin();
  for(; it!=clusters.end(); it++) {
    int count = (**it).get_count();
    counts.push_back(count);
  }
  return counts;
}

double View::calc_cluster_vector_logp(vector<double> vd, Cluster which_cluster, double &crp_logp_delta, double &data_logp_delta) const {
  int cluster_count = which_cluster.get_count();
  double score_delta;
  // NOTE: non-mutating, so presume vector is not in state
  // so use num_vectors, not num_vectors - 1
  // should try to cache counts in some way
  crp_logp_delta = numerics::calc_cluster_crp_logp(cluster_count,
						   num_vectors,
						   crp_alpha);
  data_logp_delta = which_cluster.calc_predictive_logp(vd);
  score_delta = crp_logp_delta + data_logp_delta;
  return score_delta;
}

vector<double> View::calc_cluster_vector_logps(vector<double> vd) const {
  vector<double> logps;
  set<Cluster*>::iterator it = clusters.begin();
  double crp_logp_delta, data_logp_delta;
  for(; it!=clusters.end(); it++) {
    logps.push_back(calc_cluster_vector_logp(vd, **it, crp_logp_delta, data_logp_delta));
  }
  Cluster empty_cluster(num_cols);
  logps.push_back(calc_cluster_vector_logp(vd, empty_cluster, crp_logp_delta, data_logp_delta));
  return logps;
}

double View::score_crp() const {
  vector<int> cluster_counts = get_cluster_counts();
  return numerics::calc_crp_alpha_conditional(cluster_counts, crp_alpha, num_vectors, true);
}

vector<double> View::score_crp(vector<double> alphas_to_score) const {
  vector<int> cluster_counts = get_cluster_counts();
  vector<double> crp_scores;
  vector<double>::iterator it = alphas_to_score.begin();
  for(; it!=alphas_to_score.end(); it++) {
    double alpha_to_score = *it;
    double this_crp_score = numerics::calc_crp_alpha_conditional(cluster_counts, alpha_to_score, num_vectors, true);
    crp_scores.push_back(this_crp_score);
  }
  return crp_scores;
}

std::vector<double> View::calc_hyper_conditionals(int which_col, std::string which_hyper, std::vector<double> hyper_grid) const {
  setCp::iterator it;
  vector<vector<double> > vec_vec;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    vector<double> logps = (**it).calc_hyper_conditionals(which_col, which_hyper, hyper_grid);
    vec_vec.push_back(logps);
  }
  
  return std_vector_sum(vec_vec);
}

double View::set_hyper(int which_col, string which_hyper, double new_value) {
  setCp::iterator it;
  double data_score_delta = 0;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    data_score_delta += (**it).set_hyper(which_col, which_hyper, new_value);
  }
  data_score += data_score_delta;
  return data_score_delta;
}

void View::transition_hyper(int which_col, std::string which_hyper, vector<double> hyper_grid) {
  //
  // draw new hyper
  vector<double> unorm_logps = calc_hyper_conditionals(which_col, which_hyper, hyper_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  double new_hyper_value = hyper_grid[draw];
  //
  // update all clusters
  double delta_data_score = 0;
  setCp::iterator it;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    delta_data_score += (**it).set_hyper(which_col, which_hyper, new_hyper_value);
  }
  //
  // update score
  data_score += delta_data_score;
}

void View::transition_hyper(int which_col, std::string which_hyper) {
  vector<double> hyper_grid = get_hyper_grid(which_col, which_hyper);
  transition_hyper(which_col, which_hyper, hyper_grid);
}

void View::transition_hypers(int which_col) {
  vector<string> hyper_strings = get_hyper_strings();
  // FIXME: use own shuffle so its seed controlled
  std::random_shuffle(hyper_strings.begin(), hyper_strings.end());
  for(vector<string>::iterator it=hyper_strings.begin(); it!=hyper_strings.end(); it++) {
    string which_hyper = *it;
    transition_hyper(which_col, which_hyper);
  }
}

double View::set_alpha(double new_alpha) {
  double crp_score_0 = crp_score;
  crp_alpha = new_alpha;
  crp_score = score_crp();
  return crp_score - crp_score_0;
}

Cluster& View::get_new_cluster() {
  Cluster *p_new_cluster = new Cluster(num_cols);
  clusters.insert(p_new_cluster);
  return *p_new_cluster;
}

double View::insert(vector<double> vd, Cluster& which_cluster, int row_idx) {
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

double View::insert(vector<double> vd, int row_idx) {
  vector<double> unorm_logps = calc_cluster_vector_logps(vd);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  Cluster &which_cluster = get_cluster(draw);
  double score_delta = insert(vd, which_cluster, row_idx);
  return score_delta;
}

double View::remove(vector<double> vd, int row_idx) {
  Cluster &which_cluster = *(cluster_lookup[row_idx]);
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

void View::remove_if_empty(Cluster& which_cluster) {
  if(which_cluster.get_count()==0) {
    clusters.erase(clusters.find(&which_cluster));
    delete &which_cluster;
  }
}

void View::transition_z(vector<double> vd, int row_idx) {
  remove(vd, row_idx);
  insert(vd, row_idx);
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

void View::transition_crp_alpha() {
  // to make score_crp not calculate absolute, need to track score deltas
  // and apply delta to crp_score
  vector<double> unorm_logps = score_crp(crp_alpha_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  crp_alpha = crp_alpha_grid[draw];
  crp_score = unorm_logps[draw];
}

vector<int> View::shuffle_row_indices() {
  // can't use std::random_shuffle b/c need to control seed
  vector<int> original_order;
  map<int, Cluster*>::iterator it = cluster_lookup.begin();
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
  set<Cluster*>::iterator it = clusters.begin();
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
