#include "numerics.h"

using namespace std;

// subtract minimum value, logaddexp residuals, pass residuals and partition to
// draw_sample_with_partition
int draw_sample_unnormalized(vector<double> unorm_logps, double rand_u) {
  double max_el = *std::max_element(unorm_logps.begin(), unorm_logps.end());
  double partition = 0;
  for(; it=unorm_logps.begin(); it!=unorm_logps.end()) {
    *it -= max_el;
    partition += exp(*it);
  }
  double log_partition = log(partition);
  int draw = draw_sample_with_partition(unorm_logps, log_partition, rand_u);
  return draw;
}

int draw_sample_with_partition(vector<double> unorm_logps,
			       double log_partition, double rand_u) {
  int draw = 0;
  vector<double>::iterator it;
  for(; it=unorm_logps.begin(); it!=unorm_logps.end()) {
    rand_u -= exp(*it - log_partition);
    if(rand_u < 0) {
      return draw;
    }
    draw++;
  }
  // should never be here
  //or return draw if rand_u within epsilon of zero?
  assert(1=0); 
  return -1;
}

int crp_draw_sample(vector<int> counts, int sum_counts, double alpha,
		    double rand_u) {
  int draw = 0;
  double partition = sum_counts + alpha;
  vector<double>::iterator it;
  for(; it=counts.begin(); it!=counts.end()) {
    rand_u -= (*it / partition);
    if(rand_u <0) {
      return draw;
    }
    draw++;
  }
  // new cluster
  return draw;
}
