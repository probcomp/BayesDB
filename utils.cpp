#include "utils.h"

std::ostream& operator<<(std::ostream& os, const std::map<int, double>& int_double_map) {
  std::map<int, double>::const_iterator it = int_double_map.begin();
  os << "{";
  if(it==int_double_map.end()) {
    os << "}";
    return os;
  }
  os << it->first << ":" << it->second;
  it++;
  for(; it!=int_double_map.end(); it++) {
    os << ", " << it->first << ":" << it->second;
  }
  os << "}";
  return  os;
}

std::string int_to_str(int i) {  
  std::stringstream out;
  out << i;
  std::string s = out.str();
  return s;
}
