#ifndef GUARD_randomnumbergenerator_h
#define GUARD_randomnumbergenerator_h

#include <boost/random/mersenne_twister.hpp>
#include <boost/random/normal_distribution.hpp>
#include <boost/random/variate_generator.hpp>
#include <ctime>

/////////////////////////
// from runModel_v2.cpp
class RandomNumberGenerator
{
public:
  RandomNumberGenerator() : _engine(0), _dist(_engine)
  //RandomNumberGen() : _engine(std::time_t(0)), _dist(_engine)
  {
  }

  //////////////////////////////////
  // return a random real between 
  // 0 and 1 with uniform dist
  double next()
  {
    return _dist();
  }

  //////////////////////////////
  // return a random int bewteen 
  // zero and max - 1 with uniform
  // dist if called with same max
  int nexti(int max)
  {
    double D = (double)max;
    return (int)std::floor((next() * D));
  }

  void set_seed(std::time_t seed) {
    _engine.seed(seed);
  }
protected:
   // Mersenne Twister
  boost::mt19937  _engine;
  // uniform Distribution
  boost::uniform_01<boost::mt19937> _dist;
};

#endif // GUARD_randomnumbergenerator_h
