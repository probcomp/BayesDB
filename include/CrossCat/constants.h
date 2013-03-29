#ifndef GUARD_constants_h
#define GUARD_constants_h

#include <limits> // MAX_INT
#include <string>

static const int MAX_INT = std::numeric_limits<int>::max();
static const double NaN = 0./0.;
static const std::string MULTINOMIAL_DATATYPE = "symmetric_dirichlet_discrete";
static const std::string CONTINUOUS_DATATYPE = "normal_inverse_gamma";
static const std::string continuous_key = "nu";
static const std::string multinomial_key = "dirichlet_alpha";
static const std::string TOGETHER = "together";
static const std::string FROM_THE_PRIOR = "from_the_prior";
static const std::string APART = "apart";

#endif // GUARD_constants_h
