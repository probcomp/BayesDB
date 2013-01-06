#ifndef GUARD_numerics_h
#define GUARD_numerics_h

#include <vector>
#include "Suffstats.h"
#include "Cluster.h"

template <class T> class Cluster;
template <class T> class Suffstats;

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

  double calc_continuous_logp(const int count,
			      const double r, const double nu, const double s,
			      const double log_Z_0);
  double calc_continuous_data_logp(int count,
				   double sum_x, double sum_x_sq,
				   double r, double nu,
				   double s, double mu,
				   double el, 
				   double score_0);

}

#endif //GUARD_numerics_h
