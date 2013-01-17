#include "MultinomialComponentModel.h"

using namespace std;

MultinomialComponentModel::MultinomialComponentModel(map<string, double> &in_hypers) {
  count = 0;
  score = 0;
  p_hypers = &in_hypers;
  init_suffstats();
  set_log_Z_0();
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

double MultinomialComponentModel::calc_element_predictive_logp(string element) const {
  int K;
  double dirichlet_alpha;
  get_hyper_values(K, dirichlet_alpha);
  double logp = numerics::calc_multinomial_predictive_logp(element,
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
  if(which_hyper="dirichlet_alpha") {
    return numerics::calc_multinomial_dirichlet_alpha_conditional(hyper_grid,
								  count,
								  counts,
								  K);
  } else {
    // error condition
  }
}

double MultinomialComponentModel::insert_element(string element) {
  map<string, double>::iterator it = suffstats.find(element);
  if(it==suffstats.end()) {
    suffstats[element] = 0;
  }
  double score_delta = calc_element_predictive_logp(element);
  suffstats[element] += 1;
  score += score_delta;
  return score_delta;
}

double MultinomialComponentModel::remove_element(string element) {
  suffstats[element] -= 1;
  double score_delta = calc_element_predictive_logp(element);
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
  log_Z_0 = 0;
}

void MultinomialComponentModel::init_suffstats() {
}

void MultinomialComponentModel::get_hyper_values(int &K,
						 double &dirichlet_alpha) const {
  K = get(*p_hypers, (string) "K");
  dirichlet_alpha = get(*p_hypers, (string) "dirichlet_alpha");
}

void MultinomialComponentModel::get_suffstats(int &count_out,
					      map<string, double> &counts) const {
  count_out = count;
  counts = suffstats; // a copy of the counts?
}
