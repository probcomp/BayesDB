#include "State.h"

using namespace std;

// num_cols should be set in constructor
State::State(const MatrixD &data, vector<int> global_row_indices,
	     vector<int> global_col_indices, int N_GRID, int SEED) : rng(SEED) {
  crp_alpha = 0.8;
  construct_hyper_grids(data, N_GRID);
  init_hypers(global_col_indices);
  init_views(data, global_row_indices, global_col_indices);
}

State::~State() {
  remove_all();
}

int State::get_num_cols() const {
  return view_lookup.size();
}

int State::get_num_views() const {
  return views.size();
}

vector<int> State::get_view_counts() const {
  vector<int> view_counts;
  set<View*>::iterator it;
  for(it=views.begin(); it!=views.end(); it++) {
    View &v = (**it);
    int view_num_cols = v.get_num_cols();
    view_counts.push_back(view_num_cols);
  }
  return view_counts;
}

double State::insert_feature(int feature_idx, vector<double> feature_data,
			     View &which_view) {
  map<string, double> &hypers = hypers_m[feature_idx];
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 which_view,
							 crp_logp_delta,
							 data_logp_delta,
							 hypers);
  vector<int> data_global_row_indices = create_sequence(feature_data.size());
  which_view.insert_col(feature_data, data_global_row_indices, feature_idx,
			hypers);
  view_lookup[feature_idx] = &which_view;
  crp_score += crp_logp_delta;
  data_score += data_logp_delta;
  return score_delta;
}

double State::sample_insert_feature(int feature_idx, vector<double> feature_data,
				    View &singleton_view) {
  // map<string, double> hypers = singleton_view
  map<string, double> &hypers = hypers_m[feature_idx];
  vector<double> unorm_logps = calc_feature_view_predictive_logps(feature_data,
								  feature_idx);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  View &which_view = get_view(draw);
  double score_delta = insert_feature(feature_idx, feature_data, which_view);
  remove_if_empty(singleton_view);
  return score_delta;
}

double State::remove_feature(int feature_idx, vector<double> feature_data,
			     View* &p_singleton_view) {
  map<string, double> &hypers = hypers_m[feature_idx];
  map<int,View*>::iterator it = view_lookup.find(feature_idx);
  assert(it!=view_lookup.end());
  View &which_view = *(it->second);
  view_lookup.erase(it);
  int view_num_cols = which_view.get_num_cols();
  double data_logp_delta = which_view.remove_col(feature_idx);
  double crp_logp_delta, other_data_logp_delta;
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 which_view,
							 crp_logp_delta,
							 other_data_logp_delta,
							 hypers);
  //
  if(view_num_cols==1) {
    p_singleton_view = &which_view;
  } else {
    p_singleton_view = &get_new_view();
  }
  crp_score -= crp_logp_delta;
  data_score -= data_logp_delta;
  assert(abs(other_data_logp_delta-data_logp_delta)<1E-6);
  return score_delta;
}

double State::transition_feature(int feature_idx, vector<double> feature_data) {
  double score_delta = 0;
  View *p_singleton_view;
  score_delta += remove_feature(feature_idx, feature_data, p_singleton_view);
  View &singleton_view = *p_singleton_view;
  score_delta += sample_insert_feature(feature_idx, feature_data, singleton_view);
  return score_delta;
}

double State::transition_features(const MatrixD &data) {
  double score_delta = 0;
  vector<int> feature_indices = create_sequence(data.size2());
  vector<int>::iterator it;
  for(it=feature_indices.begin(); it!=feature_indices.end(); it++) {
    int feature_idx = *it;
    vector<double> feature_data = extract_col(data, feature_idx);
    score_delta += transition_feature(feature_idx, feature_data);
  }
  return score_delta;
}

View& State::get_new_view() {
  View *p_new_view = new View();
  views.insert(p_new_view);
  return *p_new_view;
}

View& State::get_view(int view_idx) {
  assert(view_idx <= views.size());
  bool not_new = view_idx < views.size();
  if(not_new) {
    set<View*>::iterator it = views.begin();
    std::advance(it, view_idx);
    return **it;
  } else {
    // This shouldn't happen anymore
    assert(1==0);
    return get_new_view();
  }
}

void State::remove_if_empty(View& which_view) {
  if(which_view.get_num_cols()==0) {
    views.erase(views.find(&which_view));
    which_view.remove_all();
    delete &which_view;
  }
}

void State::remove_all() {
  view_lookup.empty();
  set<View*>::iterator it = views.begin();
  while(it!=views.end()) {
    View &which_view = **it;
    which_view.remove_all();
    views.erase(views.find(&which_view));
    delete &which_view;
    it = views.begin();
  }
}

double State::get_crp_alpha() const {
  return crp_alpha;
}

double State::get_crp_score() const {
  return crp_score;
}

double State::get_data_score() const {
  return data_score;
}

double State::get_marginal_logp() const {
  return crp_score + data_score;
}

double State::transition_view_i(int which_view,
				map<int, vector<double> > row_data_map) {
  // assumes views set ordering stays constant between calls
  set<View*>::iterator it = views.begin();
  std::advance(it, which_view);
  View &v = **it;
  double score_delta = v.transition(row_data_map);
  data_score += score_delta;
  return score_delta;
}

double State::transition_views(const MatrixD &data) {
  vector<int> global_column_indices = create_sequence(data.size2());
  //
  double score_delta = 0;
  // ordering doesn't matter, don't need to shuffle
  for(int view_idx=0; view_idx<get_num_views(); view_idx++) {
    View &v = get_view(view_idx);
    vector<int> view_cols = get_indices_to_reorder(global_column_indices,
						   v.global_to_local);
    const MatrixD data_subset = extract_columns(data, view_cols);
    map<int, vector<double> > data_subset_map = construct_data_map(data_subset);
    score_delta += transition_view_i(view_idx, data_subset_map);
  }
  return score_delta;
}

double State::calc_feature_view_predictive_logp(vector<double> col_data, View v,
						double &crp_log_delta,
						double &data_log_delta,
						map<string, double> hypers) const {
  int view_column_count = v.get_num_cols();
  int num_columns = get_num_cols();
  crp_log_delta = numerics::calc_cluster_crp_logp(view_column_count, num_columns,
						  crp_alpha);
  //
  vector<int> data_global_row_indices = create_sequence(col_data.size());
  // pass singleton_view down to here, or at least hypers
  data_log_delta = v.calc_column_predictive_logp(col_data,
						 data_global_row_indices,
						 hypers);
  //
  double score_delta = data_log_delta + crp_log_delta;
  return score_delta;
}

vector<double> State::calc_feature_view_predictive_logps(vector<double> col_data,
							 int global_col_idx) const {
  vector<double> logps;
  map<string, double> hypers = get(hypers_m, global_col_idx);
  set<View*>::iterator it;
  double crp_log_delta, data_log_delta;
  for(it=views.begin(); it!=views.end(); it++) {
    View &v = **it;
    double score_delta = calc_feature_view_predictive_logp(col_data, v,
							   crp_log_delta,
							   data_log_delta,
							   hypers);
    logps.push_back(score_delta);
  }
  return logps;
}

double State::calc_crp_marginal() const {
  vector<int> view_counts = get_view_counts();
  int num_cols = get_num_cols();
  return numerics::calc_crp_alpha_conditional(view_counts, crp_alpha, num_cols,
					      true);
					      
}

vector<double> State::calc_crp_marginals(vector<double> alphas_to_score) const {
  vector<int> view_counts = get_view_counts();
  vector<double> crp_scores;
  vector<double>::iterator it = alphas_to_score.begin();
  int num_cols = get_num_cols();
  for(; it!=alphas_to_score.end(); it++) {
    double alpha_to_score = *it;
    double this_crp_score = numerics::calc_crp_alpha_conditional(view_counts,
								 alpha_to_score,
								 num_cols,
								 true);
    crp_scores.push_back(this_crp_score);
  }
  return crp_scores;
}

void State::SaveResult() {}

double State::transition_crp_alpha() {
  // to make score_crp not calculate absolute, need to track score deltas
  // and apply delta to crp_score
  double crp_score_0 = get_crp_score();
  vector<double> unorm_logps = calc_crp_marginals(crp_alpha_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  crp_alpha = crp_alpha_grid[draw];
  crp_score = unorm_logps[draw];
  double crp_score_delta = crp_score - crp_score_0;
  return crp_score_delta;
}

double State::transition(const MatrixD &data) {
  vector<int> which_transitions = create_sequence(3);
  //FIXME: use own shuffle so seed control is in effect
  std::random_shuffle(which_transitions.begin(), which_transitions.end());
  double score_delta = 0;
  vector<int>::iterator it;
  cout << "group_by_value(view_lookup): " << group_by_value(view_lookup) << endl;
  for(it=which_transitions.begin(); it!=which_transitions.end(); it++) {
    int which_transition = *it;
    if(which_transition==0) {
      score_delta += transition_views(data);
    } else if(which_transition==1) {
      score_delta += transition_features(data);
    } else if(which_transition==2) {
      score_delta += transition_crp_alpha();
    }
  }
  return score_delta;
}

void State::construct_hyper_grids(const MatrixD data, int N_GRID) {
  // some helper variables for hyper grids
  vector<double> paramRange = linspace(0.03, .97, N_GRID/2);
  int APPEND_N = (N_GRID + 1) / 2;
  int data_num_cols = data.size2();
  // constrcut alpha grid
  vector<double> crp_alpha_grid_append = log_linspace(1., data_num_cols,
						      APPEND_N);
  crp_alpha_grid = append(paramRange, crp_alpha_grid_append);
}
 
double State::draw_rand_u() {
  return rng.next();
}

int State::draw_rand_i(int max) {
  return rng.nexti(max);
}

map<string, double> State::get_default_hypers() const {
  map<string, double> hypers;
  hypers["r"] = r0_0;
  hypers["nu"] = nu0_0;
  hypers["s"] = s0_0;
  hypers["mu"] = mu0_0;
  return hypers;
}

void State::init_hypers(vector<int> global_col_indices) {
  vector<int>::iterator gci_it;
  for(gci_it=global_col_indices.begin();gci_it!=global_col_indices.end(); gci_it++) {
    int global_col_idx = *gci_it;
    hypers_m[global_col_idx] = get_default_hypers();
  }
}

void State::init_views(const MatrixD &data, vector<int> global_row_indices,
		       vector<int> global_col_indices) {
  vector<vector<int> > init_column_partition;
  init_column_partition = determine_crp_init(global_col_indices, crp_alpha, rng);
  //
  vector<vector<int> >::iterator cp_it;
  for(cp_it=init_column_partition.begin(); cp_it!=init_column_partition.end();
      cp_it++) {
    vector<int> column_indices = *cp_it;
    const MatrixD data_subset = extract_columns(data, column_indices);
    View *p_v = new View(data_subset, global_row_indices, column_indices,
			 hypers_m);
    views.insert(p_v);
    vector<int>::iterator ci_it;
    for(ci_it=column_indices.begin(); ci_it!=column_indices.end(); ci_it++) {
      int column_index = *ci_it;
      view_lookup[column_index] = p_v;
    }
  }
}
