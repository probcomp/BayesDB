#include "ComponentModel.h"

using namespace std;

// virtuals that should be component model specific
double ComponentModel::calc_marginal_logp() const { assert(0); return NaN; }
double ComponentModel::calc_element_predictive_logp(double element) const { assert(0); return NaN; }
vector<double> ComponentModel::calc_hyper_conditionals(string which_hyper,
						       vector<double> hyper_grid) const
{ assert(0); vector<double> vd; return vd; }
//
double ComponentModel::insert_element(double element) { assert(0); return NaN; }
double ComponentModel::remove_element(double element) { assert(0); return NaN; }
double ComponentModel::incorporate_hyper_update() { assert(0); return NaN; }
void ComponentModel::set_log_Z_0() { assert(0); }
void ComponentModel::init_suffstats() { assert(0); }

map<string, double> ComponentModel::get_hypers() const {
  return *p_hypers;
}

int ComponentModel::get_count() const {
  return count;
}

map<string, double> ComponentModel::get_suffstats() const {
  return suffstats;
}

std::ostream& operator<<(std::ostream& os, const ComponentModel& cm) {
  os << cm.to_string() << endl;
  return os;
}

string ComponentModel::to_string(string join_str) const {
  stringstream ss;
  ss << "count: " << count << join_str;
  ss << "suffstats: " << suffstats << join_str;
  ss << "hypers: " << *p_hypers << join_str;
  ss << "marginal logp: " << calc_marginal_logp();
  return ss.str();
}
