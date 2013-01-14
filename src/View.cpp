#include "View.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
#include <boost/numeric/ublas/io.hpp>
typedef boost::numeric::ublas::matrix<double> MatrixD;

using namespace std;

typedef set<Cluster*> setCp;

//FIXME: add constructor with ranges as arguments, rather than recalculate
View::View(MatrixD data, vector<int> global_row_indices,
	   vector<int> global_col_indices, int N_GRID) {
  assert(global_row_indices.size()==data.size1());
  assert(global_col_indices.size()==data.size2());
  global_to_local = construct_lookup_map(global_col_indices);
  construct_hyper_grids(data, global_col_indices, N_GRID);
  std::vector<std::vector<int> > crp_init_cluster_indices_v;
  //
  crp_alpha = 3;
  crp_score = 0;
  data_score = 0;
  //
  crp_init_cluster_indices_v = determine_crp_init(global_row_indices, crp_alpha,
						  rng);
  int num_clusters = crp_init_cluster_indices_v.size();
  int local_row_idx = 0;
  for(int cluster_idx=0; cluster_idx<num_clusters; cluster_idx++) {
    cout << "View::View: creating cluster_idx: " << cluster_idx << endl << flush;
    std::vector<int> cluster_indices = crp_init_cluster_indices_v[cluster_idx];
    int cluster_num_rows = cluster_indices.size();
    for(int cluster_row_idx=0; cluster_row_idx<cluster_num_rows; cluster_row_idx++) {
      int global_row_idx = global_row_indices[local_row_idx];
      std::vector<double> row_data = extract_row(data, local_row_idx);
      Cluster &which_cluster = get_cluster(cluster_idx);
      cout << "View::View: inserting global_row_idx: " << global_row_idx << endl << flush;
      insert_row(row_data, which_cluster, global_row_idx);
      local_row_idx++;
    }
  }
}

View::View() {
  // when actually used, hyper grid needs to be set up
  // construct_hyper_grids(data, global_col_indices, N_GRID);
  //
  crp_alpha = 3;
  crp_score = 0;
  data_score = 0;
}

double View::get_num_vectors() const {
  return cluster_lookup.size();
}

double View::get_num_cols() const {
  return global_to_local.size();
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
  map<string, double> ret_map = (**it).get_model(col_idx).get_hypers();
  return ret_map;
}

vector<double> View::get_hyper_grid(int global_col_idx, std::string which_hyper) {
  vector<double> hyper_grid;
  if(which_hyper=="r") {
    hyper_grid = r_grid;
  } else if (which_hyper=="nu") {
    hyper_grid = nu_grid;
  } else if (which_hyper=="s") {
    hyper_grid = s_grids[global_col_idx];
  } else if (which_hyper=="mu") {
    hyper_grid = mu_grids[global_col_idx];
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

double View::calc_cluster_vector_logp(vector<double> vd, Cluster which_cluster,
				      double &crp_logp_delta,
				      double &data_logp_delta) const {
  int cluster_count = which_cluster.get_count();
  double score_delta;
  int num_vectors = get_num_vectors();
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
    logps.push_back(calc_cluster_vector_logp(vd, **it, crp_logp_delta,
					     data_logp_delta));
  }
  Cluster empty_cluster(get_num_cols());
  logps.push_back(calc_cluster_vector_logp(vd, empty_cluster, crp_logp_delta,
					   data_logp_delta));
  return logps;
}

double View::score_crp() const {
  int num_vectors = get_num_vectors();
  vector<int> cluster_counts = get_cluster_counts();
  return numerics::calc_crp_alpha_conditional(cluster_counts, crp_alpha,
					      num_vectors, true);
}

vector<double> View::score_crp(vector<double> alphas_to_score) const {
  int num_vectors = get_num_vectors();
  vector<int> cluster_counts = get_cluster_counts();
  vector<double> crp_scores;
  vector<double>::iterator it = alphas_to_score.begin();
  for(; it!=alphas_to_score.end(); it++) {
    double alpha_to_score = *it;
    double this_crp_score = numerics::calc_crp_alpha_conditional(cluster_counts,
								 alpha_to_score,
								 num_vectors,
								 true);
    crp_scores.push_back(this_crp_score);
  }
  return crp_scores;
}

std::vector<double> View::calc_hyper_conditionals(int which_col,
						  std::string which_hyper,
						  std::vector<double> hyper_grid) const {
  setCp::iterator it;
  vector<vector<double> > vec_vec;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    vector<double> logps = (**it).calc_hyper_conditionals(which_col, which_hyper,
							  hyper_grid);
    vec_vec.push_back(logps);
  }
  
  return std_vector_sum(vec_vec);
}

double View::set_hyper(int which_col, string which_hyper, double new_value) {
  setCp::iterator it;
  double score_delta = 0;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    score_delta += (**it).set_hyper(which_col, which_hyper, new_value);
  }
  data_score += score_delta;
  return score_delta;
}

double View::transition_hyper_i(int which_col, std::string which_hyper,
			      vector<double> hyper_grid) {
  //
  // draw new hyper
  vector<double> unorm_logps = calc_hyper_conditionals(which_col, which_hyper,
						       hyper_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  double new_hyper_value = hyper_grid[draw];
  //
  // update all clusters
  double score_delta = 0;
  setCp::iterator it;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    score_delta += (**it).set_hyper(which_col, which_hyper, new_hyper_value);
  }
  //
  // update score
  data_score += score_delta;
  return score_delta;
}

double View::transition_hyper_i(int which_col, std::string which_hyper) {
  vector<int> global_ordering = extract_global_ordering(global_to_local);
  int global_col_idx = global_ordering[which_col];
  vector<double> hyper_grid = get_hyper_grid(global_col_idx, which_hyper);
  double score_delta = transition_hyper_i(which_col, which_hyper, hyper_grid);
  return score_delta;
}

double View::transition_hypers_i(int which_col) {
  vector<string> hyper_strings = get_hyper_strings();
  // FIXME: use own shuffle so its seed controlled
  std::random_shuffle(hyper_strings.begin(), hyper_strings.end());
  double score_delta = 0;
  vector<string>::iterator it;
  for(it=hyper_strings.begin(); it!=hyper_strings.end(); it++) {
    string which_hyper = *it;
    score_delta += transition_hyper_i(which_col, which_hyper);
  }
  return score_delta;
}

double View::transition_hypers() {
  int num_cols = get_num_cols();
  double score_delta = 0;
  for(int local_col_idx=0; local_col_idx<num_cols; local_col_idx++) {
    score_delta += transition_hypers_i(local_col_idx);
  }
  return score_delta;
}

double View::transition(std::map<int, std::vector<double> > row_data_map) {
  vector<int> which_transitions = create_sequence(3);
  //FIXME: use own shuffle so seed control is in effect
  std::random_shuffle(which_transitions.begin(), which_transitions.end());
  double score_delta = 0;
  vector<int>::iterator it;
  for(it=which_transitions.begin(); it!=which_transitions.end(); it++) {
    int which_transition = *it;
    if(which_transition==0) {
      score_delta += transition_hypers();
    } else if(which_transition==1) {
      score_delta += transition_zs(row_data_map);
    } else if(which_transition==2) {
      score_delta += transition_crp_alpha();
    }
  }
  return score_delta;
}

double View::score_col_data(vector<double> data, vector<int> data_global_row_indices) {
  double score_delta = 0;
  setCp::iterator it;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    score_delta += (**it).score_col(data, data_global_row_indices);
  }
  return score_delta;
}

double View::set_alpha(double new_alpha) {
  double crp_score_0 = crp_score;
  crp_alpha = new_alpha;
  crp_score = score_crp();
  return crp_score - crp_score_0;
}

Cluster& View::get_new_cluster() {
  Cluster *p_new_cluster = new Cluster(get_num_cols());
  clusters.insert(p_new_cluster);
  return *p_new_cluster;
}

double View::insert_row(vector<double> vd, Cluster& which_cluster, int row_idx) {
  // NOTE: MUST use calc_cluster_vector_logp,  gets crp_score_delta as well
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_cluster_vector_logp(vd, which_cluster,
						crp_logp_delta, data_logp_delta);
  which_cluster.insert_row(vd, row_idx);
  cluster_lookup[row_idx] = &which_cluster;
  crp_score += crp_logp_delta;
  data_score += data_logp_delta;
  return score_delta;
}

double View::insert_row(vector<double> vd, int row_idx) {
  vector<double> unorm_logps = calc_cluster_vector_logps(vd);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  Cluster &which_cluster = get_cluster(draw);
  double score_delta = insert_row(vd, which_cluster, row_idx);
  return score_delta;
}

double View::remove_row(vector<double> vd, int row_idx) {
  Cluster &which_cluster = *(cluster_lookup[row_idx]);
  cluster_lookup.erase(cluster_lookup.find(row_idx));
  which_cluster.remove_row(vd, row_idx);
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_cluster_vector_logp(vd, which_cluster,
						crp_logp_delta, data_logp_delta);
  remove_if_empty(which_cluster);
  crp_score -= crp_logp_delta;
  data_score -= data_logp_delta;
  return score_delta;
}

double View::insert_col(vector<double> data,
			vector<int> data_global_row_indices,
			int global_col_idx) {
  double score_delta = 0;
  if(get_num_clusters()==0) {
    //FIXME: directly set set<Cluster*> clusters from crp init?
    // and let cluster::insert_col do the work?
  }
  setCp::iterator it;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    score_delta += (**it).insert_col(data, data_global_row_indices);
  }
  int num_cols = get_num_cols();
  global_to_local[global_col_idx] = num_cols;
  data_score += score_delta;
  cout << "View::insert_col score_delta: " << score_delta << endl;
  return score_delta;
}
 
double View::remove_col(int global_col_idx) {
  int local_col_idx = global_to_local[global_col_idx];
  //
  setCp::iterator it;
  double score_delta = 0;
  for(it=clusters.begin(); it!=clusters.end(); it++) {
    score_delta += (*it)->remove_col(local_col_idx);
  }
  // rearrange global_to_local
  std::vector<int> global_col_indices = extract_global_ordering(global_to_local);
  global_col_indices.erase(global_col_indices.begin() + local_col_idx);
  global_to_local = construct_lookup_map(global_col_indices);
  //
  data_score -= score_delta;
  cout << "View::remove_col score_delta: " << score_delta << endl;
  return score_delta;
}

void View::remove_if_empty(Cluster& which_cluster) {
  if(which_cluster.get_count()==0) {
    clusters.erase(clusters.find(&which_cluster));
    delete &which_cluster;
  }
}

double View::transition_z(vector<double> vd, int row_idx) {
  double score_delta = 0;
  score_delta += remove_row(vd, row_idx);
  score_delta += insert_row(vd, row_idx);
  return score_delta;
}

double View::transition_zs(map<int, vector<double> > row_data_map) {
  double score_delta = 0;
  vector<int> shuffled_row_indices = shuffle_row_indices();
  vector<int>::iterator it = shuffled_row_indices.begin();
  for(; it!=shuffled_row_indices.end(); it++) {
    int row_idx = *it;
    vector<double> vd = row_data_map[row_idx];
    score_delta += transition_z(vd, row_idx);
  }
  return score_delta;
}

double View::transition_crp_alpha() {
  // to make score_crp not calculate absolute, need to track score deltas
  // and apply delta to crp_score
  double crp_score_0 = get_crp_score();
  vector<double> unorm_logps = score_crp(crp_alpha_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  crp_alpha = crp_alpha_grid[draw];
  crp_score = unorm_logps[draw];
  double crp_score_delta = crp_score - crp_score_0;
  return crp_score_delta;
}

std::vector<double> View::align_data(vector<double> raw_values,
			       vector<int> global_column_indices) const {
  return reorder_per_map(raw_values, global_column_indices, global_to_local);
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

void View::print_score_matrix() {
  vector<vector<double> > scores_v;
  set<Cluster*>::iterator c_it;
  for(c_it=clusters.begin(); c_it!=clusters.end(); c_it++) {
    Cluster &c = **c_it;
    vector<double> scores = c.calc_marginal_logps();
    scores_v.push_back(scores);
  }
  cout << "crp_score: " << crp_score << endl;
  cout << "scores_v:" << endl << scores_v << endl;
}

void View::print() {
  set<Cluster*>::iterator it = clusters.begin();
  int cluster_idx = 0;
  for(; it!=clusters.end(); it++) {
    cout << "CLUSTER IDX: " << cluster_idx++ << endl;
    cout << **it << endl;
  }
  cout << "global_to_local: " << global_to_local << endl;
  cout << "crp_score: " << crp_score << ", " << "data_score: " << data_score;
  cout << ", " << "score: " << get_score() << endl;
}

void View::assert_state_consistency() {
  double tolerance = 1E-10;
  vector<int> cluster_counts = get_cluster_counts();
  int sum_via_cluster_counts = std::accumulate(cluster_counts.begin(),
					       cluster_counts.end(), 0);  
  assert(is_almost(get_num_vectors(), sum_via_cluster_counts, tolerance));
  assert(is_almost(get_crp_score(),score_crp(),tolerance));
}

double View::draw_rand_u() {
  return rng.next();
}

int View::draw_rand_i(int max) {
  return rng.nexti(max);
}

void View::construct_hyper_grids(MatrixD data, vector<int> in_col_indices,
				 int N_GRID) {
  // some helper variables for hyper grids
  vector<double> paramRange = linspace(0.03, .97, N_GRID/2);
  int APPEND_N = (N_GRID + 1) / 2;
  int data_num_vectors = data.size1();
  // constrcut alpha grid
  vector<double> crp_alpha_grid_append = log_linspace(1., data_num_vectors,
						      APPEND_N);
  crp_alpha_grid = append(paramRange, crp_alpha_grid_append);
  // construct r grid
  r_grid = crp_alpha_grid;
  //
  vector<double> nu_grid_append = log_linspace(1., data_num_vectors/2.,
					       APPEND_N);
  nu_grid = append(paramRange, nu_grid_append);
  // construct s grids
  for(int col_idx_idx=0; col_idx_idx<get_num_cols(); col_idx_idx++) {
    vector<double> col_data = extract_col(data, col_idx_idx);
    double sum_sq_deviation = calc_sum_sq_deviation(col_data);
    vector<double> s_grid_append = log_linspace(1., sum_sq_deviation, APPEND_N);
    vector<double> s_grid = append(paramRange, s_grid_append);
    //
    int col_idx = in_col_indices[col_idx_idx];
    s_grids[col_idx] = s_grid;
  }
  // construct mu grids
  for(int col_idx_idx=0; col_idx_idx<get_num_cols(); col_idx_idx++) {
    vector<double> col_data = extract_col(data, col_idx_idx);
    double min = *std::min_element(col_data.begin(), col_data.end());
    double max = *std::max_element(col_data.begin(), col_data.end());
    vector<double> mu_grid_append = linspace(min, max, APPEND_N);
    vector<double> mu_grid = append(paramRange, mu_grid_append);
    //
    int col_idx = in_col_indices[col_idx_idx];
    mu_grids[col_idx] = mu_grid;
  }
}
