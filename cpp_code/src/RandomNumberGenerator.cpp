/*
* Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*/
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
