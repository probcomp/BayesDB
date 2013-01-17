#ifndef GUARD_numerics_h
#define GUARD_numerics_h

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <string>
#include <map>
#include "assert.h"

const static double LOG_2PI = log(2.0 * M_PI);
const static double HALF_LOG_2PI = .5 * LOG_2PI;
const static double LOG_2 = log(2.0);

// use a namespce to hold all the functions?
// http://stackoverflow.com/questions/6108704/renaming-namespaces

namespace numerics {

  // sampling given vector of logps or related
  int draw_sample_unnormalized(std::vector<double> unorm_logps, double rand_u);
  int draw_sample_with_partition(std::vector<double> unorm_logps,
				 double log_partition, double rand_u);
  int crp_draw_sample(std::vector<int> counts, int sum_counts, double alpha,
		      double rand_u);

  // crp probability functions
  double calc_cluster_crp_logp(double cluster_weight, double sum_weights,
			       double alpha);
  double calc_crp_alpha_conditional(std::vector<int> counts, double alpha,
				    int sum_counts=-1, bool absolute=false);
  std::vector<double> calc_crp_alpha_conditionals(std::vector<double> grid,
						  std::vector<int> counts,
						  bool absolute=false);

  // continuous suffstats functions
  //
  //   mutators
  void insert_to_continuous_suffstats(int &count,
				      double &sum_x, double &sum_x_sq,
				      double el);
  void remove_from_continuous_suffstats(int &count,
					double &sum_x, double &sum_x_sq,
					double el);
  void update_continuous_hypers(int count,
				double sum_x, double sum_x_sq,
				double &r, double &nu,
				double &s, double &mu);
  //   calculators
  double calc_continuous_logp(int count,
			      double r, double nu, double s,
			      double log_Z_0);
  double calc_continuous_data_logp(int count,
				   double sum_x, double sum_x_sq,
				   double r, double nu,
				   double s, double mu,
				   double el, 
				   double score_0);
  std::vector<double> calc_continuous_r_conditionals(std::vector<double> r_grid,
						     int count,
						     double sum_x,
						     double sum_x_sq,
						     double nu,
						     double s,
						     double mu);
  std::vector<double> calc_continuous_nu_conditionals(std::vector<double> nu_grid,
						     int count,
						     double sum_x,
						     double sum_x_sq,
						     double r,
						     double s,
						     double mu);
  std::vector<double> calc_continuous_s_conditionals(std::vector<double> s_grid,
						     int count,
						     double sum_x,
						     double sum_x_sq,
						     double r,
						     double nu,
						     double mu);
  std::vector<double> calc_continuous_mu_conditionals(std::vector<double> mu_grid,
						      int count,
						      double sum_x,
						      double sum_x_sq,
						      double r,
						      double nu,
						      double s);
  
  // multinomial suffstats functions
  //
  //   mutators (NONE FOR NOW)
  //
  // calculators
  double calc_multinomial_marginal_logp(int count,
					std::map<std::string, double> counts,
					int K,
					double dirichlet_alpha);
  double calc_multinomial_predictive_logp(std::string element,
					  std::map<std::string, double> counts,
					  int sum_counts,
					  int K, double dirichlet_alpha);
  std::vector<double> calc_multinomial_dirichlet_alpha_conditional(std::vector<double> dirichlet_alphas,
								   std::map<std::string, double> counts,
								   int K);

} // namespace numerics

#endif //GUARD_numerics_h
