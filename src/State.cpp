#include "State.h"

typedef boost::numeric::ublas::matrix<double> MatrixD;
using namespace std;

// num_cols should be set in constructor
State::State(boost::numeric::ublas::matrix<double> data,
      std::vector<int> global_row_indices, std::vector<int> global_col_indices,
      int N_GRID) {
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

double State::get_crp_score() const {
  return crp_score;
}

double State::get_data_score() const {
  return data_score;
}

double State::get_marginal_logp() const {
  return crp_score + data_score;
}

double State::transition_features() {
  assert(1==0);
}

double State::transition_view_i(int which_view,
				std::map<int, std::vector<double> > row_data_map) {
  // assumes views set ordering stays constant between calls
  set<View*>::iterator it = views.begin();
  std::advance(it, which_view);
  View &v = **it;
  double score_delta = v.transition(row_data_map);
  data_score += score_delta;
  return score_delta;
}

double State::transition_views(std::map<int, std::vector<double> > row_data_map) {
  double score_delta = 0;
  // ordering doesn't matter, don't need to shuffle
  for(int view_idx=0; view_idx<get_num_views(); view_idx++) {
    score_delta += transition_view_i(view_idx, row_data_map);
  }
  return score_delta;
}

double State::score_crp() const {
  vector<int> view_counts = get_view_counts();
  int num_cols = get_num_cols();
  return numerics::calc_crp_alpha_conditional(view_counts, crp_alpha,
					      num_cols, true);
}

vector<double> State::score_crp(vector<double> alphas_to_score) const {
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
  vector<double> unorm_logps = score_crp(crp_alpha_grid);
  double rand_u = draw_rand_u();
  int draw = numerics::draw_sample_unnormalized(unorm_logps, rand_u);
  crp_alpha = crp_alpha_grid[draw];
  crp_score = unorm_logps[draw];
  double crp_score_delta = crp_score - crp_score_0;
  return crp_score_delta;
}

double State::transition(std::map<int, std::vector<double> > row_data_map) {
  vector<int> which_transitions = create_sequence(3);
  //FIXME: use own shuffle so seed control is in effect
  std::random_shuffle(which_transitions.begin(), which_transitions.end());
  double score_delta = 0;
  vector<int>::iterator it;
  for(it=which_transitions.begin(); it!=which_transitions.end(); it++) {
    int which_transition = *it;
    if(which_transition==0) {
      score_delta += transition_views(row_data_map);
    } else if(which_transition==1) {
      score_delta += transition_features();
    } else if(which_transition==2) {
      score_delta += transition_crp_alpha();
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
