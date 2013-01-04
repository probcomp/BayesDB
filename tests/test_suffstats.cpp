#include <iostream>
#include "Suffstats.h"

using namespace std;

typedef Suffstats<double> suffD;

int main(int argc, char** argv) {  
  cout << "Begin:: test_suffstats" << endl;

  suffD sd(1.2,2.3,3.4,4.5);
  double insert_value;

  cout << "initial suffstats" << endl;
  cout << sd << endl;

  insert_value = 0.0;
  cout << "insert value: " << insert_value << endl;
  sd.insert_el(insert_value);
  cout << sd << endl;

  insert_value = 1.0;
  cout << "insert value: " << insert_value << endl;
  sd.insert_el(insert_value);
  cout << sd << endl;

  insert_value = 1.0;
  cout << "insert value: " << insert_value << endl;
  sd.insert_el(insert_value);
  cout << sd << endl;

  insert_value = 1.0;
  cout << "insert value: " << insert_value << endl;
  sd.insert_el(insert_value);
  cout << sd << endl;

  insert_value = 3.0;
  cout << "insert value: " << insert_value << endl;
  sd.insert_el(insert_value);
  cout << sd << endl;

  cout << "Stop:: test_suffstats" << endl;
}
