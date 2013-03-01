#ifndef GUARD_constants_h
#define GUARD_constants_h

#include <limits> // MAX_INT
#include <string>

static const int MAX_INT = std::numeric_limits<int>::max();
static const double NaN = 0./0.;
static const std::string MULTINOMIAL_DATATYPE = "symmetric_dirichlet_discrete";
static const std::string CONTINUOUS_DATATYPE = "normal_inverse_gamma";


#endif // GUARD_constants_h
