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
#include "ComponentModel.h"

using namespace std;

// virtuals that should be component model specific
double ComponentModel::calc_marginal_logp() const { assert(0); return NaN; }
double ComponentModel::calc_element_predictive_logp(double element) const { assert(0); return NaN; }
double ComponentModel::calc_element_predictive_logp_constrained(double element, vector<double> constraints) const { assert(0); return NaN; }
vector<double> ComponentModel::calc_hyper_conditionals(string which_hyper,
						       vector<double> hyper_grid) const
{ assert(0); vector<double> vd; return vd; }
map<string, double> ComponentModel::_get_suffstats() const {
	assert(0); map<string, double> suffstats; return suffstats;
}
//
double ComponentModel::insert_element(double element) { assert(0); return NaN; }
double ComponentModel::remove_element(double element) { assert(0); return NaN; }
double ComponentModel::incorporate_hyper_update() { assert(0); return NaN; }
void ComponentModel::set_log_Z_0() { assert(0); }
void ComponentModel::init_suffstats() { assert(0); }

CM_Hypers ComponentModel::get_hypers() const {
  return *p_hypers;
}

int ComponentModel::get_count() const {
  return count;
}

map<string, double> ComponentModel::get_suffstats() const {
  map<string, double> suffstats_out = _get_suffstats();
  suffstats_out["N"] = count;
  return suffstats_out;
}

std::ostream& operator<<(std::ostream& os, const ComponentModel& cm) {
  os << cm.to_string() << endl;
  return os;
}

string ComponentModel::to_string(string join_str) const {
  stringstream ss;
  ss << "count: " << count << join_str;
  ss << "suffstats: " << get_suffstats() << join_str;
  ss << "hypers: " << *p_hypers << join_str;
  ss << "marginal logp: " << calc_marginal_logp();
  return ss.str();
}
