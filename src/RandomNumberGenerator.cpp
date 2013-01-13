#include "RandomNumberGenerator.h"

//////////////////////////////////
// return a random real between 
// 0 and 1 with uniform dist
double RandomNumberGenerator::next() {
  return _dist();
}

//////////////////////////////
// return a random int bewteen 
// zero and max - 1 with uniform
// dist if called with same max
int RandomNumberGenerator::nexti(int max) {
  double D = (double)max;
  return (int)std::floor((next() * D));
}

/////////////////////////////
// control the seed
void RandomNumberGenerator::set_seed(std::time_t seed) {
  _engine.seed(seed);
  boost::uniform_01<boost::mt19937> new_dist(_engine);
  _dist = new_dist;
}
