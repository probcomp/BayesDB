#include "State.h"


using namespace std;
using boost::numeric::ublas::matrix;
using boost::numeric::ublas::project;
using boost::numeric::ublas::range;


// FIXME: shouldn't need T, not really using suffstats here
State::State(const MatrixD &data,
	     vector<string> GLOBAL_COL_DATATYPES,
	     vector<int> GLOBAL_COL_MULTINOMIAL_COUNTS,
	     vector<int> global_row_indices,
	     vector<int> global_col_indices,
	     map<int, map<string, double> > HYPERS_M,
	     vector<vector<int> > column_partition,
	     double COLUMN_CRP_ALPHA,
	     vector<vector<vector<int> > > row_partition_v,
	     vector<double> row_crp_alpha_v,
	     int N_GRID, int SEED) : rng(SEED) {
  column_crp_score = 0;
  data_score = 0;
  int num_rows = data.size1();
  int num_cols = data.size2();
  global_col_datatypes = construct_lookup_map(global_col_indices,
					      GLOBAL_COL_DATATYPES);
  global_col_multinomial_counts = \
    construct_lookup_map(global_col_indices, GLOBAL_COL_MULTINOMIAL_COUNTS);
  construct_base_hyper_grids(num_rows, num_cols, N_GRID);
  // pass colmn types to construct_base_hyper_grids
  construct_column_hyper_grids(data, global_col_indices,
			       GLOBAL_COL_DATATYPES);
  //
  column_crp_alpha = COLUMN_CRP_ALPHA;
  hypers_m = HYPERS_M;
  //
  // pass columntypes
  init_views(data, global_col_datatypes,
	     global_row_indices, global_col_indices,
	     column_partition, row_partition_v, row_crp_alpha_v);
}

State::State(const MatrixD &data,
	     vector<string> GLOBAL_COL_DATATYPES,
	     vector<int> GLOBAL_COL_MULTINOMIAL_COUNTS,
	     vector<int> global_row_indices,
	     vector<int> global_col_indices,
	     string col_initialization,
	     string row_initialization,
	     int N_GRID, int SEED) : rng(SEED) {
  // FIXME: unlink these when API is updated
  if(row_initialization=="") {row_initialization = col_initialization; }
  column_crp_score = 0;
  data_score = 0;
  int num_rows = data.size1();
  int num_cols = data.size2();
  global_col_datatypes = construct_lookup_map(global_col_indices,
					      GLOBAL_COL_DATATYPES);
  global_col_multinomial_counts = \
    construct_lookup_map(global_col_indices, GLOBAL_COL_MULTINOMIAL_COUNTS);
			 
  construct_base_hyper_grids(num_rows, num_cols, N_GRID);
  construct_column_hyper_grids(data, global_col_indices,
			       GLOBAL_COL_DATATYPES);
  //
  init_base_hypers();
  init_column_hypers(global_col_indices);
  //
  init_views(data, global_col_datatypes, global_row_indices,
	     global_col_indices, col_initialization, row_initialization);
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
  string col_datatype = global_col_datatypes[feature_idx];
  map<string, double> &hypers = hypers_m[feature_idx];
  double crp_logp_delta, data_logp_delta;
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 col_datatype,
							 which_view,
							 crp_logp_delta,
							 data_logp_delta,
							 hypers);
  vector<int> data_global_row_indices = create_sequence(feature_data.size());
  which_view.insert_col(feature_data,
			data_global_row_indices, feature_idx,
			hypers);
  view_lookup[feature_idx] = &which_view;
  column_crp_score += crp_logp_delta;
  data_score += data_logp_delta;
  return score_delta;
}

double State::sample_insert_feature(int feature_idx, vector<double> feature_data,
				    View &singleton_view) {
  string col_datatype = global_col_datatypes[feature_idx];
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
  string col_datatype = global_col_datatypes[feature_idx];
  map<string, double> &hypers = hypers_m[feature_idx];
  map<int,View*>::iterator it = view_lookup.find(feature_idx);
  assert(it!=view_lookup.end());
  View &which_view = *(it->second);
  view_lookup.erase(it);
  int view_num_cols = which_view.get_num_cols();
  double data_logp_delta = which_view.remove_col(feature_idx);
  double crp_logp_delta, other_data_logp_delta;
  double score_delta = calc_feature_view_predictive_logp(feature_data,
							 col_datatype,
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
  column_crp_score -= crp_logp_delta;
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
  // FIXME: this is a hack
  // it being necessary suggests perhaps I should not be passing
  // global_row_indices and instead always assume its a sequence of 0..N
  vector<int> first_view_cluster_counts = get_view(0).get_cluster_counts();
  int num_vectors = std::accumulate(first_view_cluster_counts.begin(), first_view_cluster_counts.end(), 0);
  vector<int> global_row_indices = create_sequence(num_vectors);
  View *p_new_view = new View(global_col_datatypes,
			      global_row_indices,
			      row_crp_alpha_grid, multinomial_alpha_grid, r_grid, nu_grid, s_grids,
			      mu_grids, draw_rand_i());
  views.insert(p_new_view);
  return *p_new_view;
}

View& State::get_view(int view_idx) {
  assert(view_idx <= views.size());
  bool not_new = ((unsigned int) view_idx) < views.size();
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

double State::get_column_crp_alpha() const {
  return column_crp_alpha;
}

double State::get_column_crp_score() const {
  return column_crp_score;
}

double State::get_data_score() const {
  set<View*>::const_iterator it;
  double data_score = 0;
  for(it=views.begin(); it!=views.end(); it++) {
    double data_score_i = (**it).get_score();
    data_score += data_score_i;
  }
  return data_score;
}

double State::get_marginal_logp() const {
  return column_crp_score + get_data_score();
}

map<string, double> State::get_row_partition_model_hypers_i(int view_idx) const {
  set<View*>::const_iterator it = views.begin();
  std::advance(it, view_idx);
  return (**it).get_row_partition_model_hypers();
}

vector<int> State::get_row_partition_model_counts_i(int view_idx) const {
  set<View*>::const_iterator it = views.begin();
  std::advance(it, view_idx);
  return (**it).get_row_partition_model_counts();
}

vector<vector<map<string, double> > > State::get_column_component_suffstats_i(int view_idx) const {
  // ordering should be same as column_names
  set<View*>::const_iterator it = views.begin();
  std::advance(it, view_idx);
  assert(it!=views.end());
  return (**it).get_column_component_suffstats();
}

vector<map<string, double> > State::get_column_hypers() const {
  vector<map<string, double> > column_hypers;
  int num_cols = get_num_cols();
  map<int, map<string, double> >::const_iterator it;
  for(int global_col_idx=0; global_col_idx<num_cols; global_col_idx++) {
    it = hypers_m.find(global_col_idx);
    if(it==hypers_m.end()) continue;
    map<string, double> hypers_i = it->second;
    // FIXME: actually detect
    hypers_i["fixed"] = 0.;
    column_hypers.push_back(hypers_i);
  }
  return column_hypers;
}

map<string,double> State::get_column_partition_hypers() const {
  map<string, double> local_hypers;
  local_hypers["log_alpha"] = log(get_column_crp_alpha());
  return local_hypers;
}

vector<int> State::get_column_partition_assignments() const {
  return define_group_ordering(view_lookup, views);
}

vector<int> State::get_column_partition_counts() const {
  return get_view_counts();
}

vector<vector<int> > State::get_X_D() const {
  vector<vector<int> > X_D;
  set<View*>::iterator it;
  for(it=views.begin(); it!=views.end(); it++) {
    View &v = **it;
    vector<int> canonical_clustering = v.get_canonical_clustering();
    X_D.push_back(canonical_clustering);
  }
  return X_D;
}

map<int, set<int> > State::get_column_groups() const {
  map<View*, int> view_to_int = set_to_map(views);
  map<View*, set<int> > view_to_set = group_by_value(view_lookup);
  map<int, set<int> > view_idx_to_set;
  set<View*>::iterator it;
  for(it=views.begin(); it!=views.end(); it++) {
    View* p_v = *it;
    int view_idx = view_to_int[p_v];
    set<int> int_set = view_to_set[p_v];
    view_idx_to_set[view_idx] = int_set;
  }
  return view_idx_to_set;
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

// helper for cython
double State::transition_view_i(int which_view, const MatrixD &data) {
  vector<int> global_column_indices = create_sequence(data.size2());
  View &v = get_view(which_view);
  vector<int> view_cols = get_indices_to_reorder(global_column_indices,
						 v.global_to_local);
  const MatrixD data_subset = extract_columns(data, view_cols);
  map<int, vector<double> > data_subset_map = construct_data_map(data_subset);
  return v.transition(data_subset_map);
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
    score_delta += v.transition(data_subset_map);
  }
  return score_delta;
}


double State::transition_views_zs(const MatrixD &data) {
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
    score_delta += v.transition_zs(data_subset_map);
  }
  data_score += score_delta;
  return score_delta;
}

double State::transition_views_row_partition_hyper() {
  double score_delta = 0;
  for(int view_idx=0; view_idx<get_num_views(); view_idx++) {
    View &v = get_view(view_idx);
    score_delta += v.transition_crp_alpha();
  }
  data_score += score_delta;
  return score_delta;
}

double State::transition_views_col_hypers() {
  double score_delta = 0;
  for(int view_idx=0; view_idx<get_num_views(); view_idx++) {
    View &v = get_view(view_idx);
    score_delta += v.transition_hypers();
  }
  data_score += score_delta;
  return score_delta;
}

double State::calc_feature_view_predictive_logp(vector<double> col_data,
						string col_datatype, View v,
						double &crp_log_delta,
						double &data_log_delta,
						map<string, double> hypers) const {
  int view_column_count = v.get_num_cols();
  int num_columns = get_num_cols();
  crp_log_delta = numerics::calc_cluster_crp_logp(view_column_count, num_columns,
						  column_crp_alpha);
  //
  vector<int> data_global_row_indices = create_sequence(col_data.size());
  // pass singleton_view down to here, or at least hypers
  data_log_delta = v.calc_column_predictive_logp(col_data, col_datatype,
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
  string col_datatype = get(global_col_datatypes, global_col_idx);
  for(it=views.begin(); it!=views.end(); it++) {
    View &v = **it;
    double score_delta = calc_feature_view_predictive_logp(col_data,
							   col_datatype,
							   v,
							   crp_log_delta,
							   data_log_delta,
							   hypers);
    logps.push_back(score_delta);
  }
  return logps;
}

double State::calc_column_crp_marginal() const {
  vector<int> view_counts = get_view_counts();
  int num_cols = get_num_cols();
  return numerics::calc_crp_alpha_conditional(view_counts, column_crp_alpha,
					      num_cols, true);
}

vector<double> State::calc_column_crp_marginals(vector<double> alphas_to_score) const {
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

void State::SaveResult(string filename, int iter_idx) {
  ofstream out(filename.c_str(), ios_base::app);
  if(!out) {
    cout << "Cannot open file: " << filename << endl;
    return;
  }

  if(iter_idx!=-1) {
    out << "State" << iter_idx << endl;
  }
  View &first_view = **views.begin();
  int num_rows = first_view.get_num_vectors();
  int num_cols = view_lookup.size();
  map<View*, int> view_to_int = set_to_map(views);
  int n_grid = column_crp_alpha_grid.size();

  out << "F = " << num_cols << endl;
  out << "O = " << num_rows << endl;
 
  matrix<int> f(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    View* p_v = view_lookup[col_idx];
    f(0,col_idx) = view_to_int[p_v];
  }
  out << "f = " << f << endl;

  matrix<int> o(num_cols, num_rows, NaN); // transposed!
  set<View*>::iterator views_it = views.begin();
  for(; views_it!=views.end(); views_it++) {
    View* v_p = *views_it;
    int matrix_row_idx = view_to_int[v_p];
    vector<vector<int> > cluster_groupings = v_p->get_cluster_groupings();
    int num_clusters = cluster_groupings.size();
    for(int cluster_idx=0; cluster_idx<num_clusters; cluster_idx++) {
      vector<int> cluster_indices = cluster_groupings[cluster_idx];
      int num_elements = cluster_indices.size();
      for(int element_idx=0; element_idx<num_elements; element_idx++) {
	int row_idx = cluster_indices[element_idx];
	o(matrix_row_idx, row_idx) = cluster_idx;
      }
    }
  }
  out << "o = " << o << endl;

  matrix<double> paramPrior(1, n_grid, 1./n_grid);
  out << "paramPrior = " << paramPrior << endl;

  matrix<double> cumParamPrior(1, n_grid, 1./n_grid);
  for(unsigned int i=0; i<cumParamPrior.size2(); i++) {
    cumParamPrior(0,i) *= (i+1); 
  }
  out << "cumParamPrior = " << cumParamPrior << endl;

  matrix<double> paramRange(1, n_grid, NaN);
  out << "paramRange = " << paramRange << endl;

  
  matrix<double> crpKRange = vector_to_matrix(column_crp_alpha_grid);
  out << "crpKRange = " << crpKRange << endl;

  matrix<double> crpCRange = vector_to_matrix(row_crp_alpha_grid);
  out << "crpCRange = " << crpCRange << endl;

  matrix<double> kRange = vector_to_matrix(r_grid);
  out << "kRange = " << kRange << endl;

  matrix<double> aRange = vector_to_matrix(nu_grid);
  out << "aRange = " << aRange << endl;

  // FIXME: grids don't seem to be homogenous, so this is broken
  matrix<double> muRange(num_cols, n_grid, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    matrix<double> this_hyper_grid_m = vector_to_matrix(mu_grids[col_idx]);
    project(muRange, range(col_idx, col_idx+1), range(0, n_grid-1)) = \
      project(this_hyper_grid_m, range(0, 1), range(0, n_grid-1));
  }
  out << "muRange = " << muRange << endl;

  matrix<double> bRange(num_cols, n_grid, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    matrix<double> this_hyper_grid_m = vector_to_matrix(s_grids[col_idx]);
    project(bRange, range(col_idx, col_idx+1), range(0, n_grid-1)) =	\
      project(this_hyper_grid_m, range(0, 1), range(0, n_grid-1));
  }
  out << "bRange = " << bRange << endl;

  out << "crpK = " << column_crp_alpha << endl;

  matrix<double> crpC(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    View &v = *view_lookup[col_idx];
    crpC(0, col_idx) = v.get_crp_alpha();
  }
  out << "crpC = " << crpC << endl;

  matrix<double> NG_a(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    NG_a(0, col_idx) = hypers_m[col_idx]["nu"];
  }
  out << "NG_a = " << NG_a << endl;

  matrix<double> NG_k(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    NG_k(0, col_idx) = hypers_m[col_idx]["r"];
  }
  out << "NG_k = " << NG_k << endl;

  matrix<double> NG_b(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    NG_b(0, col_idx) = hypers_m[col_idx]["s"];
  }
  out << "NG_b = " << NG_b << endl;


  matrix<double> NG_mu(1, num_cols, NaN);
  for(int col_idx=0; col_idx<num_cols; col_idx++) {
    NG_mu(0, col_idx) = hypers_m[col_idx]["mu"];
  }
  out << "NG_mu = " << NG_mu << endl;

  out << endl;
}

double State::transition_column_crp_alpha() {
  // to make score_crp not calculate absolute, need to track score deltas
  // and apply delta to crp_score
  double crp_score_0 = get_column_crp_score();
  vector<double> unorm_logps = calc_column_crp_marginals(column_crp_alpha_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  column_crp_alpha = column_crp_alpha_grid[draw];
  column_crp_score = unorm_logps[draw];
  double crp_score_delta = column_crp_score - crp_score_0;
  return crp_score_delta;
}

double State::transition(const MatrixD &data) {
  vector<int> which_transitions = create_sequence(3);
  //FIXME: use own shuffle so seed control is in effect
  std::random_shuffle(which_transitions.begin(), which_transitions.end());
  double score_delta = 0;
  vector<int>::iterator it;
  for(it=which_transitions.begin(); it!=which_transitions.end(); it++) {
    int which_transition = *it;
    if(which_transition==0) {
      score_delta += transition_views(data);
    } else if(which_transition==1) {
      score_delta += transition_features(data);
    } else if(which_transition==2) {
      score_delta += transition_column_crp_alpha();
    }
  }
  return score_delta;
}

void State::construct_base_hyper_grids(int num_rows, int num_cols, int N_GRID) {
  row_crp_alpha_grid = create_crp_alpha_grid(num_rows, N_GRID);
  column_crp_alpha_grid = create_crp_alpha_grid(num_cols, N_GRID);
  construct_continuous_base_hyper_grids(N_GRID, num_rows, r_grid, nu_grid);
  construct_multinomial_base_hyper_grids(N_GRID, num_rows, multinomial_alpha_grid);
}

void State::construct_column_hyper_grids(const MatrixD data,
					 vector<int> global_col_indices,
					 vector<string> GLOBAL_COL_DATATYPES) {
  int N_GRID = r_grid.size();
  vector<int>::iterator it;
  for(it=global_col_indices.begin(); it!=global_col_indices.end(); it++) {
    int global_col_idx = *it;
    string col_datatype = GLOBAL_COL_DATATYPES[global_col_idx];
    if(col_datatype!=CONTINUOUS_DATATYPE) continue;
    vector<double> col_data = extract_col(data, global_col_idx);
    construct_continuous_specific_hyper_grid(N_GRID, col_data,
					     s_grids[global_col_idx],
					     mu_grids[global_col_idx]);
  }
}
 
double State::draw_rand_u() {
  return rng.next();
}

int State::draw_rand_i(int max) {
  return rng.nexti(max);
}

map<string, double> State::uniform_sample_hypers(int global_col_idx) {
  // presume all grids the same size
  int N_GRID = r_grid.size();
  string col_datatype = global_col_datatypes[global_col_idx];
  map<string, double> hypers;
  if(col_datatype==CONTINUOUS_DATATYPE) {
    hypers["r"] = r_grid[draw_rand_i(N_GRID)];
    hypers["nu"] = nu_grid[draw_rand_i(N_GRID)];
    hypers["s"] = s_grids[global_col_idx][draw_rand_i(N_GRID)];
    hypers["mu"] = mu_grids[global_col_idx][draw_rand_i(N_GRID)];
  } else if(col_datatype==MULTINOMIAL_DATATYPE) {
    hypers["dirichlet_alpha"] = multinomial_alpha_grid[draw_rand_i(N_GRID)];
    hypers["K"] = global_col_multinomial_counts[global_col_idx];
  } else {
    assert(1==0);
  }
  return hypers;
}

void State::init_base_hypers() {
  int N_GRID = column_crp_alpha_grid.size();
  column_crp_alpha = column_crp_alpha_grid[draw_rand_i(N_GRID)];
}

void State::init_column_hypers(vector<int> global_col_indices) {
  vector<int>::iterator gci_it;
  for(gci_it=global_col_indices.begin();gci_it!=global_col_indices.end(); gci_it++) {
    int global_col_idx = *gci_it;
    hypers_m[global_col_idx] = uniform_sample_hypers(global_col_idx);
  }
}

void State::init_views(const MatrixD &data,
		       map<int, string> global_col_datatypes,
		       vector<int> global_row_indices,
		       vector<int> global_col_indices,
		       vector<vector<int> > column_partition,
		       vector<vector<vector<int> > > row_partition_v,
		       vector<double> row_crp_alpha_v) {
  assert(column_partition.size()==row_partition_v.size());
  assert(column_partition.size()==row_crp_alpha_v.size());
  int num_views = column_partition.size();
  for(int view_idx=0; view_idx<num_views; view_idx++) {
    vector<int> column_indices = column_partition[view_idx];
    vector<vector<int> > row_partition = row_partition_v[view_idx];
    double row_crp_alpha = row_crp_alpha_v[view_idx];
    const MatrixD data_subset = extract_columns(data, column_indices);
    View *p_v = new View(data_subset,
			 global_col_datatypes,
			 row_partition,
			 global_row_indices, column_indices,
			 hypers_m,
			 row_crp_alpha_grid,
			 multinomial_alpha_grid, r_grid, nu_grid,
			 s_grids, mu_grids,
			 row_crp_alpha,
			 draw_rand_i());
    views.insert(p_v);
    vector<int>::iterator ci_it;
    for(ci_it=column_indices.begin(); ci_it!=column_indices.end(); ci_it++) {
      int column_index = *ci_it;
      view_lookup[column_index] = p_v;
    }
  }
}

void State::init_views(const MatrixD &data,
		       map<int, string> global_col_datatypes,
		       vector<int> global_row_indices,
		       vector<int> global_col_indices,
		       string col_initialization,
		       string row_initialization) {
  // generate column paritition
  vector<vector<int> > column_partition;
  column_partition = draw_crp_init(global_col_indices, column_crp_alpha, rng,
				   col_initialization);
  // generate row paritition
  vector<vector<vector<int> > > row_partition_v;
  vector<double> row_crp_alpha_v;
  int num_views = column_partition.size();
  int N_GRID = row_crp_alpha_grid.size();
  for(int view_idx=0; view_idx<num_views; view_idx++) {
    double row_crp_alpha = row_crp_alpha_grid[rng.nexti(N_GRID)];
    vector<vector<int> > row_partition;
    row_partition = draw_crp_init(global_row_indices, row_crp_alpha, rng,
				  row_initialization);
    row_crp_alpha_v.push_back(row_crp_alpha);
    row_partition_v.push_back(row_partition);
  }
  init_views(data, global_col_datatypes, global_row_indices,
	     global_col_indices, column_partition, row_partition_v,
	     row_crp_alpha_v);
	     
}

std::ostream& operator<<(std::ostream& os, const State& s) {
  os << s.to_string() << endl;
  return os;
}

string State::to_string(string join_str, bool top_level) const {
  stringstream ss;
  if(!top_level) {
    int view_idx = 0;
    set<View*>::const_iterator it;
    ss << "========" << std::endl;
    for(it=views.begin(); it!=views.end(); it++) {
      View v = **it;
      ss << "view idx: " << view_idx++ << endl;
      ss << v << endl;
      ss << "========" << std::endl;
    }    
  }
  ss << "column_crp_alpha: " << column_crp_alpha;
  ss << "; column_crp_score: " << column_crp_score;
  ss << "; data_score: " << get_data_score();
  return ss.str();
}
