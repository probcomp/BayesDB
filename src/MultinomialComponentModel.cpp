#include "MultinomialComponentModel.h"

using namespace std;

MultinomialComponentModel::MultinomialComponentModel(map<string, double> &in_hypers) {
  count = 0;
  score = 0;
  p_hypers = &in_hypers;
  init_suffstats();
  set_log_Z_0();
}

MultinomialComponentModel::MultinomialComponentModel(map<string, double> &in_hypers,
						     int count_in,
						     std::map<std::string, double> counts) {
  count = 0;
  score = 0;
  p_hypers = &in_hypers;
  set_log_Z_0();
  // set suffstats
  count = count_in;
  suffstats = counts;
  score = calc_marginal_logp();
}

double MultinomialComponentModel::calc_marginal_logp() const {
  int count;
  map<string, double> counts;
  int K;
  double dirichlet_alpha;
  get_hyper_values(K, dirichlet_alpha);
  get_suffstats(count, counts);
  return numerics::calc_multinomial_marginal_logp(count, counts, K, dirichlet_alpha);
}

double MultinomialComponentModel::calc_element_predictive_logp(double element) const {
  int K;
  double dirichlet_alpha;
  get_hyper_values(K, dirichlet_alpha);
  string element_str = stringify(element);
  double logp = numerics::calc_multinomial_predictive_logp(element_str,
							   suffstats, count,
							   K, dirichlet_alpha);
  return logp;
}

vector<double> MultinomialComponentModel::calc_hyper_conditionals(string which_hyper, vector<double> hyper_grid) const {
  int count;
  map<string, double> counts;
  int K;
  double dirichlet_alpha;
  get_hyper_values(K, dirichlet_alpha);
  get_suffstats(count, counts);
  if(which_hyper=="dirichlet_alpha") {
    return numerics::calc_multinomial_dirichlet_alpha_conditional(hyper_grid,
								  count,
								  counts,
								  K);
  } else {
    // error condition
    cout << "MultinomialComponentModel::calc_hyper_conditional: bad value for which_hyper=" << which_hyper << endl;
    assert(0);
    vector<double> vd;
    return vd;
  }
}

double MultinomialComponentModel::insert_element(double element) {
  string element_str = stringify(element);
  if(!in(suffstats, element_str)) {
    suffstats[element_str] = 0;
  }
  double score_delta = calc_element_predictive_logp(element);
  suffstats[element_str] += 1;
  count += 1;
  score += score_delta;
  return score_delta;
}

double MultinomialComponentModel::remove_element(double element) {
  string element_str = stringify(element);
  suffstats[element_str] -= 1;
  double score_delta = calc_element_predictive_logp(element);
  count -= 1;
  score -= score_delta;
  return score_delta;
}

double MultinomialComponentModel::incorporate_hyper_update() {
  double score_0 = score;
  // hypers[which_hyper] = value; // set by owner of hypers object
  score = calc_marginal_logp();
  double score_delta = score - score_0;
  return score_delta;
}

void MultinomialComponentModel::set_log_Z_0() {
  log_Z_0 = calc_marginal_logp();
}

void MultinomialComponentModel::init_suffstats() {
  
}

void MultinomialComponentModel::get_hyper_values(int &K,
						 double &dirichlet_alpha) const {
  K = get(*p_hypers, (string) "K");
  dirichlet_alpha = get(*p_hypers, (string) "dirichlet_alpha");
}

double MultinomialComponentModel::get_draw(int random_seed) const {
  // get modified suffstats
  int count;
  map<string, double> counts;
  int K;
  double dirichlet_alpha;
  get_hyper_values(K, dirichlet_alpha);
  get_suffstats(count, counts);
  // get a random draw
  boost::mt19937  _engine(random_seed);
  boost::uniform_01<boost::mt19937> _dist(_engine);
  double uniform_draw = _dist();
  //
  vector<string> keys;
  vector<double> log_counts_for_draw;
  map<string, double>::const_iterator it;
  for(it=counts.begin(); it!=counts.end(); it++) {
    string key = it->first;
    int count_for_draw = it->second;
    // "update" counts by adding dirichlet alpha to each value
    count_for_draw += dirichlet_alpha;
    keys.push_back(key);
    log_counts_for_draw.push_back(log(count_for_draw));
  }
  int key_idx = numerics::draw_sample_unnormalized(log_counts_for_draw,
						   uniform_draw);
  double draw = intify(keys[key_idx]);
  return draw;
}

void MultinomialComponentModel::get_suffstats(int &count_out,
					      map<string, double> &counts) const {
  count_out = count;
  counts = suffstats; // a copy of the counts?
}
