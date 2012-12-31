#ifndef GUARD_numerics_h
#define GUARD_numerics_h

int draw_sample_unnormalized(vector<double> unorm_logps, double rand_u);

int draw_sample_with_partition(vector<double> unorm_logps, double log_partition,
			       double rand_u);

int crp_draw_sample(vector<int> counts, int sum_counts, double alpha,
		    double rand_u);

// FIXME: should move suffstats updates to here

double calc_alpha_conditional();
double calc_beta_conditional();

#endif //GUARD_numerics_h
