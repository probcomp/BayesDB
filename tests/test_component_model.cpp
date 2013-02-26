#include <iostream>
#include "ComponentModel.h"
#include "ContinuousComponentModel.h"
#include "MultinomialComponentModel.h"

using namespace std;

int main() {
  cout << "Hello World" << endl;

  map<string, double> continuous_hypers;
  continuous_hypers["r"] = 10;
  continuous_hypers["nu"] = 10;
  continuous_hypers["s"] = 10;
  continuous_hypers["mu"] = 10;
  map<string, double> multinomial_hypers;
  multinomial_hypers["K"] = 10;
  multinomial_hypers["dirichlet_alpha"] = 10;

  ComponentModel ccm = ContinuousComponentModel(continuous_hypers);
  ComponentModel mcm = MultinomialComponentModel(multinomial_hypers);

  cout << "Goodbye World" << endl;
}
