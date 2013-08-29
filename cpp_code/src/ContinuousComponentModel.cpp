/*
* Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*/
#include "ContinuousComponentModel.h"
using namespace std;

ContinuousComponentModel::ContinuousComponentModel(CM_Hypers &in_hypers) {
  count = 0;
  score = 0;
  p_hypers = &in_hypers;
  hyper_r = (*p_hypers)["r"];
  hyper_nu = (*p_hypers)["nu"];
  hyper_s = (*p_hypers)["s"];
  hyper_mu = (*p_hypers)["mu"];
  init_suffstats();
  set_log_Z_0();
}

ContinuousComponentModel::ContinuousComponentModel(CM_Hypers &in_hypers, int COUNT, double SUM_X, double SUM_X_SQ) {
  count = COUNT;
  sum_x = SUM_X;
  sum_x_squared = SUM_X_SQ;
  p_hypers = &in_hypers;
  hyper_r = (*p_hypers)["r"];
  hyper_nu = (*p_hypers)["nu"];
  hyper_s = (*p_hypers)["s"];
  hyper_mu = (*p_hypers)["mu"];
  set_log_Z_0();
  score = calc_marginal_logp();
}

void ContinuousComponentModel::get_hyper_doubles(double &r, double &nu,
	       	double &s, double &mu) const {
  r = hyper_r;
  nu = hyper_nu;
  s = hyper_s;
  mu = hyper_mu;
}

double ContinuousComponentModel::calc_marginal_logp() const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);
  return numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
}

double ContinuousComponentModel::calc_element_predictive_logp(double element) const {
  if(isnan(element)) return 0;
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  //
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared, element);
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);


  double logp_prime = numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
  return logp_prime - score;
}

double ContinuousComponentModel::calc_element_predictive_logp_constrained(double element, vector<double> constraints) const {
  if(isnan(element)) return 0;
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  //
  for(int constraint_idx=0; constraint_idx<constraints.size();
      constraint_idx++) {
    double constraint = constraints[constraint_idx];
    numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared,
					     constraint);
  }
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);
  double baseline = numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
  //
  get_hyper_doubles(r, nu, s, mu);
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared, element);
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);
  double updated = numerics::calc_continuous_logp(count, r, nu, s, log_Z_0);
  double predictive_logp = updated - baseline;
  return predictive_logp;
}

vector<double> ContinuousComponentModel::calc_hyper_conditionals(string which_hyper, vector<double> hyper_grid) const {
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  
  if(which_hyper=="r") {
    return numerics::calc_continuous_r_conditionals(hyper_grid, count, sum_x,
						    sum_x_squared, nu, s, mu);
  } else if(which_hyper=="nu"){
    return numerics::calc_continuous_nu_conditionals(hyper_grid, count, sum_x,
						     sum_x_squared, r, s, mu);
  } else if(which_hyper=="s"){
    return numerics::calc_continuous_s_conditionals(hyper_grid, count, sum_x,
						    sum_x_squared, r, nu, mu);
  } else if(which_hyper=="mu"){
    return numerics::calc_continuous_mu_conditionals(hyper_grid, count, sum_x,
						     sum_x_squared, r, nu, s);
  } else {
    // error condition
    vector<double> error;
    return error;
  }
}

double ContinuousComponentModel::insert_element(double element) {
  if(isnan(element)) return 0;
  double score_0 = score;
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared, element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::remove_element(double element) {
  if(isnan(element)) return 0;
  double score_0 = score;
  numerics::remove_from_continuous_suffstats(count, sum_x, sum_x_squared, element);
  score = calc_marginal_logp();
  double delta_score = score - score_0;
  return delta_score;
}

double ContinuousComponentModel::incorporate_hyper_update() {
  hyper_r = get(*p_hypers, (string) "r");
  hyper_nu = get(*p_hypers, (string) "nu");
  hyper_s = get(*p_hypers, (string) "s");
  hyper_mu = get(*p_hypers, (string) "mu");
  double score_0 = score;
  // hypers[which_hyper] = value; // set by owner of hypers object
  set_log_Z_0();
  score = calc_marginal_logp();
  double score_delta = score - score_0;
  return score_delta;
}

void ContinuousComponentModel::set_log_Z_0() {
  double r, nu, s, mu;
  get_hyper_doubles(r, nu, s, mu);
  log_Z_0 = numerics::calc_continuous_logp(0, r, nu, s, 0);
}

void ContinuousComponentModel::init_suffstats() {
	sum_x = 0.;
	sum_x_squared = 0.;
}

void ContinuousComponentModel::get_suffstats(int &count_out, double &sum_x_out,
					     double &sum_x_squared_out) const {
  count_out = count;
  sum_x_out = sum_x;
  sum_x_squared_out = sum_x_squared;
}

double ContinuousComponentModel::get_draw(int random_seed) const {
  // get modified suffstats
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);
  //
  boost::mt19937  _engine(random_seed);
  boost::uniform_01<boost::mt19937> _dist(_engine);
  boost::random::student_t_distribution<double> student_t(nu);
  double student_t_draw = student_t(_dist);
  // FIXME: should 's' be divided by 2 as well here to reconcile Murphy with Teh?
  // http://www.cs.ubc.ca/~murphyk/Teaching/CS340-Fall07/reading/NG.pdf
  // http://www.stats.ox.ac.uk/~teh/research/notes/GaussianInverseGamma.pdf
  double coeff = sqrt((s * (r+1)) / (nu / 2. * r));
  double draw = student_t_draw * coeff + mu;
  return draw;
}

double ContinuousComponentModel::get_draw_constrained(int random_seed, vector<double> constraints) const {
  // get modified suffstats
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  for(int constraint_idx=0; constraint_idx<constraints.size();
      constraint_idx++) {
    double constraint = constraints[constraint_idx];
    numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared,
					     constraint);
  }
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);
  //
  boost::mt19937  _engine(random_seed);
  boost::uniform_01<boost::mt19937> _dist(_engine);
  boost::random::student_t_distribution<double> student_t(nu);
  double student_t_draw = student_t(_dist);
  double coeff = sqrt((s * (r+1)) / (nu / 2. * r));
  double draw = student_t_draw * coeff + mu;
  return draw;
}

// For simple predictive probability
double ContinuousComponentModel::get_predictive_cdf(double element, vector<double> constraints) const {
  // get modified suffstats
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  for(int constraint_idx=0; constraint_idx<constraints.size();
      constraint_idx++) {
    double constraint = constraints[constraint_idx];
    numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared,
               constraint);
  }
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);

  boost::math::students_t dist(nu);
  double coeff = sqrt((s * (r+1)) / (nu / 2. * r));
  // manipulate the number so it will fit in the standard t (reverse of the draw proceedure)
  double rev_draw = (element-mu)/ coeff ;
  double cdfval = boost::math::cdf(dist, rev_draw);

  return cdfval;
}

// For simple predictive probability
double ContinuousComponentModel::get_predictive_pdf(double element, vector<double> constraints) const {
  // get modified suffstats
  double r, nu, s, mu;
  int count;
  double sum_x, sum_x_squared;
  get_hyper_doubles(r, nu, s, mu);
  get_suffstats(count, sum_x, sum_x_squared);
  for(int constraint_idx=0; constraint_idx<constraints.size();
      constraint_idx++) {
    double constraint = constraints[constraint_idx];
    numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_squared,
               constraint);
  }
  numerics::update_continuous_hypers(count, sum_x, sum_x_squared, r, nu, s, mu);

  
  boost::math::students_t dist(nu);
  double coeff = sqrt((s * (r+1)) / (nu / 2. * r));
  // manipulate the number so it will fit in the standard t (reverse of the draw proceedure)
  double rev_draw = (element-mu)/ coeff ;
  double pdfval = boost::math::pdf(dist, rev_draw);

  return pdfval;
}

map<string, double> ContinuousComponentModel::_get_suffstats() const {
	map<string, double> suffstats;
	suffstats["sum_x"] = sum_x;
	suffstats["sum_x_squared"] = sum_x_squared;
  	return suffstats;
}

