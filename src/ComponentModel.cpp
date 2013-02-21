#include "ComponentModel.h"

using namespace std;

// virtuals that should be component model specific
double ComponentModel::calc_marginal_logp() const { assert(0); return NaN; }
double ComponentModel::calc_element_predictive_logp(double element) const { assert(0); return NaN; }
vector<double> ComponentModel::calc_hyper_conditionals(string which_hyper,
						       vector<double> hyper_grid)
{ assert(0); }
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
  os << "count: " << cm.count << endl;
  os << "suffstats: " << cm.suffstats << endl;
  os << "hypers: " << *cm.p_hypers << endl;
  os << "marginal logp: " << cm.calc_marginal_logp() << endl;
  return os;
}

string ComponentModel::to_string() {
  stringstream ss;
  ss << *this;
  return ss.str();
}
