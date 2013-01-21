#ifndef GUARD_randomnumbergenerator_h
#define GUARD_randomnumbergenerator_h

#include <boost/random/mersenne_twister.hpp>
#include <boost/random/normal_distribution.hpp>
#include <boost/random/variate_generator.hpp>
#include <ctime>
#include <limits>

const int MAX_INT = std::numeric_limits<int>::max();

/////////////////////////
// from runModel_v2.cpp
class RandomNumberGenerator
{
public:
 RandomNumberGenerator() : _engine(0), _dist(_engine) {};
 RandomNumberGenerator(int SEED) : _engine(SEED), _dist(_engine) {};
  double next();
  int nexti(int max=MAX_INT);
  void set_seed(std::time_t seed);
 protected:
  // Mersenne Twister
  boost::mt19937  _engine;
  // uniform Distribution
  boost::uniform_01<boost::mt19937> _dist;
};

#endif // GUARD_randomnumbergenerator_h
