#include "numerics.h"

#include <cmath>
#include <algorithm>
#include <numeric>
#include "assert.h"
using namespace std;


// subtract minimum value, logaddexp residuals, pass residuals and partition to
// draw_sample_with_partition
int numerics::draw_sample_unnormalized(vector<double> unorm_logps, double rand_u) {
  double max_el = *std::max_element(unorm_logps.begin(), unorm_logps.end());
  double partition = 0;
  vector<double>::iterator it = unorm_logps.begin();
  for(; it!=unorm_logps.end(); it++) {
    *it -= max_el;
    partition += exp(*it);
  }
  double log_partition = log(partition);
  int draw = numerics::draw_sample_with_partition(unorm_logps, log_partition,
						  rand_u);
  return draw;
}

int numerics::draw_sample_with_partition(vector<double> unorm_logps,
			       double log_partition, double rand_u) {
  int draw = 0;
  vector<double>::iterator it = unorm_logps.begin();
  for(; it!=unorm_logps.end(); it++) {
    rand_u -= exp(*it - log_partition);
    if(rand_u < 0) {
      return draw;
    }
    draw++;
  }
  // FIXME: should this fail?
  assert(rand_u < 1E-10);
  return draw;
}

// draw_sample_with_partition w/o exp() of ratio and no test for p(last)
// only useful for crp_init or supercluster swapping since no data component
int numerics::crp_draw_sample(vector<int> counts, int sum_counts, double alpha,
		    double rand_u) {
  int draw = 0;
  double partition = sum_counts + alpha;

  vector<int>::iterator it = counts.begin();
  for(; it!=counts.end(); it++) {
    rand_u -= (*it / partition);
    if(rand_u <0) {
      return draw;
    }
    draw++;
  }
  // new cluster
  return draw;
}

// p(alpha | clusters)
double numerics::calc_crp_alpha_conditional(std::vector<int> counts,
					    double alpha, int sum_counts,
					    bool absolute) {
  int num_clusters = counts.size();
  if(sum_counts==-1) {
    sum_counts = std::accumulate(counts.begin(), counts.end(), 0);
  }
  double logp = lgamma(alpha)			\
    + num_clusters * log(alpha)			\
    - lgamma(alpha + sum_counts);
  // absolute necessary for determining true distribution rather than relative
  if(absolute) {
    double sum_log_gammas = 0;
    std::vector<int>::iterator it = counts.begin();
    for(; it!=counts.end(); it++) {
      sum_log_gammas += lgamma(*it);
    }
    logp += sum_log_gammas;
  }
  return logp;
}

// helper for may calls to calc_crp_alpha_conditional
std::vector<double> numerics::calc_crp_alpha_conditionals(std::vector<double> grid,
							  std::vector<int> counts,
							  bool absolute) {
  int sum_counts = std::accumulate(counts.begin(), counts.end(), 0);
  std::vector<double> logps;
  std::vector<double>::iterator it = grid.begin();
  for(; it!=grid.end(); it++) {
    double alpha = *it;
    double logp = numerics::calc_crp_alpha_conditional(counts, alpha,
						       sum_counts, absolute);
    logps.push_back(logp);
  }
  // note: prior distribution must still be added
  return logps;
}

// p(z=cluster | alpha, clusters)
double numerics::calc_cluster_crp_logp(double cluster_weight, double sum_weights,
				       double alpha) {
  if(cluster_weight == 0) {
    cluster_weight = alpha;
  }
  double log_numerator = log(cluster_weight);
  // presumes data has already been removed from the model
  double log_denominator = log(sum_weights + alpha);
  double log_probability = log_numerator - log_denominator;
  return log_probability;
}

void numerics::insert_to_continuous_suffstats(int &count,
					      double &sum_x, double &sum_x_sq,
					      double el) {
  count += 1;
  sum_x += el;
  sum_x_sq += el * el;
}

void numerics::remove_from_continuous_suffstats(int &count,
						double &sum_x, double &sum_x_sq,
						double el) {
  count -= 1;
  sum_x -= el;
  sum_x_sq -= el * el;
}

/*
  r' = r + n
  nu' = nu + n
  m' = m + (X-nm)/(r+n)
  s' = s + C + rm**2 - r'm'**2
*/
void numerics::update_continuous_hypers(int count,
					double sum_x, double sum_x_sq,
					double &r, double &nu,
					double &s, double &mu) {
  double r_prime = r + count;
  double nu_prime = nu + count;
  double mu_prime =  ((r * mu) + sum_x) / r_prime;
  double s_prime = s + sum_x_sq \
    + (r * mu * mu) \
    - (r_prime * mu_prime * mu_prime);
  //
  r = r_prime;
  nu = nu_prime;
  s = s_prime;
  mu = mu_prime;
}

double calc_continuous_log_Z(double r, double nu, double s)  {
  double nu_over_2 = .5 * nu;
  return nu_over_2 * (LOG_2 - log(s))			\
    + HALF_LOG_2PI					\
    - .5 * log(r)					\
    + lgamma(nu_over_2);
}

double numerics::calc_continuous_logp(int count,
				      double r, double nu,
				      double s,
				      double log_Z_0) {
  return -count * HALF_LOG_2PI + calc_continuous_log_Z(r, nu, s) - log_Z_0;
}

double numerics::calc_continuous_data_logp(int count,
					   double sum_x, double sum_x_sq,
					   double r, double nu,
					   double s, double mu,
					   double el,
					   double score_0) {
  numerics::insert_to_continuous_suffstats(count, sum_x, sum_x_sq, el);
  numerics::update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
  double logp = numerics::calc_continuous_logp(count, r, nu, s, score_0);
  return logp;
}

vector<double> numerics::calc_continuous_r_conditionals(std::vector<double> r_grid,
							int count,
							double sum_x,
							double sum_x_sq,
							double nu,
							double s,
							double mu) {
  std::vector<double> logps;
  std::vector<double>::iterator it;
  for(it=r_grid.begin(); it!=r_grid.end(); it++) {
    double r_prime = *it;
    double nu_prime = nu;
    double s_prime = s;
    double mu_prime = mu;
    double log_Z_0 = calc_continuous_log_Z(r_prime, nu_prime, s_prime);
    update_continuous_hypers(count, sum_x, sum_x_sq,
			     r_prime, nu_prime, s_prime, mu_prime);
    double logp = numerics::calc_continuous_logp(count,
						 r_prime, nu_prime, s_prime,
						 log_Z_0);
    logps.push_back(logp);
  }
  return logps;
}
