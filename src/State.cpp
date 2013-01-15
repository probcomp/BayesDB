#include "State.h"

using namespace std;

// num_cols should be set in constructor
State::State(MatrixD &data, vector<int> global_row_indices,
	     vector<int> global_col_indices, int N_GRID) {
  crp_alpha = 0.8;
  int num_rows = data.size1();
  construct_hyper_grids(data, N_GRID);
  vector<vector<int> > column_partition;
  column_partition = determine_crp_init(global_col_indices, crp_alpha, rng);
  vector<vector<int> >::iterator cp_it;
  for(cp_it=column_partition.begin(); cp_it!=column_partition.end(); cp_it++) {
    vector<int> column_indices = *cp_it;
    cout << "State::State: column_indices: " << column_indices << endl;
    MatrixD data_subset = extract_columns(data, column_indices);
    View *p_v = new View(data_subset, global_row_indices, column_indices);
    views.insert(p_v);
    vector<int>::iterator ci_it;
    for(ci_it=column_indices.begin(); ci_it!=column_indices.end(); ci_it++) {
      int column_index = *ci_it;
      view_lookup[column_index] = p_v;
    }
  }
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
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 which_view,
							 crp_logp_delta,
							 data_logp_delta);
  vector<int> data_global_row_indices = create_sequence(feature_data.size());
  which_view.insert_col(feature_data, data_global_row_indices, feature_idx);
  view_lookup[feature_idx] = &which_view;
  crp_score += crp_logp_delta;
  data_score += data_logp_delta;
  return score_delta;
}

double State::insert_feature(int feature_idx, vector<double> feature_data) {
  vector<double> unorm_logps = calc_feature_view_predictive_logps(feature_data);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  View &which_view = get_view(draw);
  double score_delta = insert_feature(feature_idx, feature_data, which_view);
  return score_delta;
}

double State::remove_feature(int feature_idx, vector<double> feature_data) {
  map<int,View*>::iterator it = view_lookup.find(feature_idx);
  assert(it!=view_lookup.end());
  View &which_view = *(it->second);
  view_lookup.erase(it);
  double data_logp_delta_doublecheck = which_view.remove_col(feature_idx);
  //
  double crp_logp_delta, data_logp_delta;
  // FIXME: when inserting into a new feature, hypers must be the same as before
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 which_view,
							 crp_logp_delta,
							 data_logp_delta);
  //
  remove_if_empty(which_view);
  crp_score -= crp_logp_delta;
  data_score -= data_logp_delta;
  //
  if(data_logp_delta_doublecheck!=data_logp_delta) {
    cout << "data_logp_delta_doublecheck: " << data_logp_delta_doublecheck;
    cout << ", data_logp_delta: " << data_logp_delta << endl;
  }
  //assert(data_logp_delta_doublecheck==data_logp_delta);
  return score_delta;
}

double State::transition_feature(int feature_idx, vector<double> feature_data) {
  double score_delta = 0;
  score_delta += remove_feature(feature_idx, feature_data);
  score_delta += insert_feature(feature_idx, feature_data);
  return score_delta;
}

double State::transition_features(MatrixD &data) {
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
    return get_new_view();
  }
}

void State::remove_if_empty(View& which_view) {
  if(which_view.get_num_cols()==0) {
    views.erase(views.find(&which_view));
    delete &which_view;
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

double State::transition_views(MatrixD &data) {
  vector<int> global_column_indices = create_sequence(data.size2());
  //
  double score_delta = 0;
  // ordering doesn't matter, don't need to shuffle
  for(int view_idx=0; view_idx<get_num_views(); view_idx++) {
    View &v = get_view(view_idx);
    cout << "transitioning view: " << &v << " with global_to_local: " << v.global_to_local << endl;
    vector<int> view_cols = get_indices_to_reorder(global_column_indices,
						   v.global_to_local);
    MatrixD data_subset = extract_columns(data, view_cols);
    map<int, vector<double> > data_subset_map = construct_data_map(data_subset);
    score_delta += transition_view_i(view_idx, data_subset_map);
  }
  return score_delta;
}

double State::calc_feature_view_predictive_logp(vector<double> col_data, View v,
						double &crp_log_delta,
						double &data_log_delta) const {
  int view_column_count = v.get_num_cols();
  int num_columns = get_num_cols();
  crp_log_delta = numerics::calc_cluster_crp_logp(view_column_count, num_columns,
						  crp_alpha);
  //
  vector<int> data_global_row_indices = create_sequence(col_data.size());
  data_log_delta = v.calc_column_predictive_logp(col_data,
						 data_global_row_indices);
  //
  double score_delta = data_log_delta + crp_log_delta;
  return score_delta;
}

vector<double> State::calc_feature_view_predictive_logps(vector<double> col_data) const {
  vector<double> logps;
  set<View*>::iterator it;
  double crp_log_delta, data_log_delta;
  for(it=views.begin(); it!=views.end(); it++) {
    View &v = **it;
    double score_delta = calc_feature_view_predictive_logp(col_data, v,
							   crp_log_delta,
							   data_log_delta);
    logps.push_back(score_delta);
  }
  View empty_view = View();
  double score_delta = calc_feature_view_predictive_logp(col_data, empty_view,
							 crp_log_delta,
							 data_log_delta);
  logps.push_back(score_delta);
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

double State::transition(MatrixD &data) {
  vector<int> which_transitions = create_sequence(3);
  //FIXME: use own shuffle so seed control is in effect
  std::random_shuffle(which_transitions.begin(), which_transitions.end());
  double score_delta = 0;
  vector<int>::iterator it;
  // FIXME: not printing something on the line below causes seg fault
  // cout << "view_lookup: " << view_lookup << endl;
  // cout << "other thing to test segfault: " << views << endl;
  for(it=which_transitions.begin(); it!=which_transitions.end(); it++) {
    int which_transition = *it;
    if(which_transition==0) {
      cout << "State::transition: trying transition_views" << endl << flush;
      cout << "view_lookup: " << view_lookup << endl;
      score_delta += transition_views(data);
      cout << "State::transition: done transition_views" << endl << flush;
    } else if(which_transition==1) {
      cout << "State::transition: trying transition_features" << endl << flush;
      score_delta += transition_features(data);
      cout << "State::transition: done transition_features" << endl << flush;
      cout << "view_lookup: " << view_lookup << endl;
    } else if(which_transition==2) {
      cout << "State::transition: trying transition_crp_alpha" << endl << flush;
      score_delta += transition_crp_alpha();
      cout << "State::transition: done transition_crp_alpha" << endl << flush;
    }
  }
  return score_delta;
}

void State::construct_hyper_grids(MatrixD data, int N_GRID) {
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
