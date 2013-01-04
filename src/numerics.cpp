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

/*
  r' = r + n
  nu' = nu + n
  m' = m + (X-nm)/(r+n)
  s' = s + C + rm**2 - r'm'**2
*/
double numerics::insert_to_continuous_suffstats(int &count,
						double &r, double &nu,
						double &s, double &mu,
						double el) {
  count += 1;
  //
  double r_prime = r + 1;
  double nu_prime = nu + 1;
  double mu_prime = mu + (el - mu) / r_prime;
  double s_prime = s + pow(el, 2)		\
    + (r * pow(mu, 2))				\
    - r_prime * pow(mu_prime, 2);
  //
  nu = nu_prime;
  r = r_prime;
  mu = mu_prime;
  s = s_prime;
}

double numerics::remove_from_continuous_suffstats(int &count,
						  double &r, double &nu,
						  double &s, double &mu,
						  double el) {
  count -= 1;
  //
  double r_prime = r - 1;
  double nu_prime = nu - 1;
  double mu_prime = (r * mu - el) / r_prime;
  double s_prime = s - pow(el, 2)		\
    + (r * pow(mu, 2))				\
    - r_prime * pow(mu_prime, 2);
  //
  nu = nu_prime;
  r = r_prime;
  mu = mu_prime;
  s = s_prime;
}

double calc_continuous_log_Z(const double r, const double nu, const double s)  {
  double nu_over_2 = .5 * nu;
  return nu_over_2 * (LOG_2 - log(s))			\
    + HALF_LOG_2PI					\
    - .5 * log(r)					\
    + lgamma(nu_over_2);
}

double numerics::calc_continuous_logp(const int count,
				      const double r, const double nu,
				      const double s,
				      const double log_Z_0) {
  return -count * HALF_LOG_2PI + calc_continuous_log_Z(r, nu, s) - log_Z_0;
}

double numerics::calc_continuous_suffstats_data_logp(int count,
						     double r, double nu,
						     double s, double mu,
						     double el,
						     double log_Z) {
  numerics::insert_to_continuous_suffstats(count, r, nu, s, mu, el);
  double logp = numerics::calc_continuous_logp(count, r, nu, s, log_Z);
  return logp;
}
