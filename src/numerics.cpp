#include "numerics.h"

using namespace std;

namespace numerics {

  double calc_crp_alpha_hyperprior(double alpha) {
    double logp = 0;
    // invert the effect of log gridding
    // logp += +log(alpha);
    return logp;
  }

  double calc_continuous_hyperprior(double r, double nu, double s) {
    double logp = 0;
    // invert the effect of log gridding
    // logp += log(r) + log(nu) + log(s);
    // // 
    // logp += -(log(r) + log(nu) + log(s)) / 16. / 3.;
    return logp;
  }

  // subtract minimum value, logaddexp residuals, pass residuals and partition to
  // draw_sample_with_partition
  int draw_sample_unnormalized(vector<double> unorm_logps, double rand_u) {
    double max_el = *std::max_element(unorm_logps.begin(), unorm_logps.end());
    double partition = 0;
    vector<double>::iterator it = unorm_logps.begin();
    for(; it!=unorm_logps.end(); it++) {
      *it -= max_el;
      partition += exp(*it);
    }
    double log_partition = log(partition);
    int draw = draw_sample_with_partition(unorm_logps, log_partition,
					  rand_u);
    return draw;
  }
  
  int draw_sample_with_partition(vector<double> unorm_logps,
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
  int crp_draw_sample(vector<int> counts, int sum_counts, double alpha,
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
  double calc_crp_alpha_conditional(std::vector<int> counts,
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
    logp += calc_crp_alpha_hyperprior(alpha);
    return logp;
  }

  // helper for may calls to calc_crp_alpha_conditional
  std::vector<double> calc_crp_alpha_conditionals(std::vector<double> grid,
						  std::vector<int> counts,
						  bool absolute) {
    int sum_counts = std::accumulate(counts.begin(), counts.end(), 0);
    std::vector<double> logps;
    std::vector<double>::iterator it = grid.begin();
    for(; it!=grid.end(); it++) {
      double alpha = *it;
      double logp = calc_crp_alpha_conditional(counts, alpha,
					       sum_counts, absolute);
      logps.push_back(logp);
    }
    // note: prior distribution must still be added
    return logps;
  }

  // p(z=cluster | alpha, clusters)
  double calc_cluster_crp_logp(double cluster_weight, double sum_weights,
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

  void insert_to_continuous_suffstats(int &count,
				      double &sum_x, double &sum_x_sq,
				      double el) {
    count += 1;
    sum_x += el;
    sum_x_sq += el * el;
  }

  void remove_from_continuous_suffstats(int &count,
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
  void update_continuous_hypers(int count,
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
    double log_Z = nu_over_2 * (LOG_2 - log(s))		\
      + HALF_LOG_2PI					\
      - .5 * log(r)					\
      + lgamma(nu_over_2);
    log_Z += calc_continuous_hyperprior(r, nu, s);
    return log_Z;
  }

  double calc_continuous_logp(int count,
			      double r, double nu,
			      double s,
			      double log_Z_0) {
    return -count * HALF_LOG_2PI + calc_continuous_log_Z(r, nu, s) - log_Z_0;
  }

  double calc_continuous_data_logp(int count,
				   double sum_x, double sum_x_sq,
				   double r, double nu,
				   double s, double mu,
				   double el,
				   double score_0) {
    insert_to_continuous_suffstats(count, sum_x, sum_x_sq, el);
    update_continuous_hypers(count, sum_x, sum_x_sq, r, nu, s, mu);
    double logp = calc_continuous_logp(count, r, nu, s, score_0);
    return logp;
  }

  vector<double> calc_continuous_r_conditionals(std::vector<double> r_grid,
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
      double logp = calc_continuous_logp(count,
					 r_prime, nu_prime, s_prime,
					 log_Z_0);
      logps.push_back(logp);
    }
    return logps;
  }

  vector<double> calc_continuous_nu_conditionals(std::vector<double> nu_grid,
						 int count,
						 double sum_x,
						 double sum_x_sq,
						 double r,
						 double s,
						 double mu) {
    std::vector<double> logps;
    std::vector<double>::iterator it;
    for(it=nu_grid.begin(); it!=nu_grid.end(); it++) {
      double r_prime = r;
      double nu_prime = *it;
      double s_prime = s;
      double mu_prime = mu;
      double log_Z_0 = calc_continuous_log_Z(r_prime, nu_prime, s_prime);
      update_continuous_hypers(count, sum_x, sum_x_sq,
			       r_prime, nu_prime, s_prime, mu_prime);
      double logp = calc_continuous_logp(count,
					 r_prime, nu_prime, s_prime,
					 log_Z_0);
      logps.push_back(logp);
    }
    return logps;
  }

  vector<double> calc_continuous_s_conditionals(std::vector<double> s_grid,
						int count,
						double sum_x,
						double sum_x_sq,
						double r,
						double nu,
						double mu) {
    std::vector<double> logps;
    std::vector<double>::iterator it;
    for(it=s_grid.begin(); it!=s_grid.end(); it++) {
      double r_prime = r;
      double nu_prime = nu;
      double s_prime = *it;
      double mu_prime = mu;
      double log_Z_0 = calc_continuous_log_Z(r_prime, nu_prime, s_prime);
      update_continuous_hypers(count, sum_x, sum_x_sq,
			       r_prime, nu_prime, s_prime, mu_prime);
      double logp = calc_continuous_logp(count,
					 r_prime, nu_prime, s_prime,
					 log_Z_0);
      logps.push_back(logp);
    }
    return logps;
  }

  vector<double> calc_continuous_mu_conditionals(std::vector<double> mu_grid,
						 int count,
						 double sum_x,
						 double sum_x_sq,
						 double r,
						 double nu,
						 double s) {
    std::vector<double> logps;
    std::vector<double>::iterator it;
    for(it=mu_grid.begin(); it!=mu_grid.end(); it++) {
      double r_prime = r;
      double nu_prime = nu;
      double s_prime = s;
      double mu_prime = *it;
      double log_Z_0 = calc_continuous_log_Z(r_prime, nu_prime, s_prime);
      update_continuous_hypers(count, sum_x, sum_x_sq,
			       r_prime, nu_prime, s_prime, mu_prime);
      double logp = calc_continuous_logp(count,
					 r_prime, nu_prime, s_prime,
					 log_Z_0);
      logps.push_back(logp);
    }
    return logps;
  }

  double calc_multinomial_marginal_logp(int count,
					const map<string, double> counts,
					int K,
					double dirichlet_alpha) {
    double sum_lgammas = 0;
    map<string, double>::const_iterator it;
    for(it=counts.begin(); it!=counts.end(); it++) {
      int label_count = it->second;
      sum_lgammas += lgamma(label_count + dirichlet_alpha);
    }
    int missing_labels = K - counts.size();
    if(missing_labels != 0) {
      sum_lgammas += missing_labels * lgamma(dirichlet_alpha);
    }
    double marginal_logp = lgamma(K * dirichlet_alpha)	\
      - K * lgamma(dirichlet_alpha)		\
      + sum_lgammas				\
      - lgamma(count + K * dirichlet_alpha);
    return marginal_logp;
  }

  double calc_multinomial_predictive_logp(string element,
					  map<string, double> counts,
					  int sum_counts,
					  int K, double dirichlet_alpha) {
    map<string, double>::iterator it = counts.find(element);
    double numerator = dirichlet_alpha;
    if(it!=counts.end()) {
      numerator += counts[element];
    }
    double denominator = sum_counts + K * dirichlet_alpha;
    return numerator / denominator;
  }

  vector<double> calc_multinomial_dirichlet_alpha_conditional(vector<double> dirichlet_alpha_grid,
						      int count,
						      map<string, double> counts,
						      int K) {
    vector<double> logps;
    vector<double>::iterator it;
    for(it=dirichlet_alpha_grid.begin(); it!=dirichlet_alpha_grid.end(); it++) {
      double dirichlet_alpha = *it;
      double logp = calc_multinomial_marginal_logp(count, counts, K,
						   dirichlet_alpha);
      logps.push_back(logp);
    }
    return logps;
  }
  
} // namespace numerics
