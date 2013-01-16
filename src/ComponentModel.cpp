#include "ComponentModel.h"

using namespace std;

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
