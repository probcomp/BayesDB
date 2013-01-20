#include <iostream>
#include <map>
#include <vector>
#include <string>
#include "MultinomialComponentModel.h"
#include "RandomNumberGenerator.h"
#include "utils.h"


using namespace std;

typedef MultinomialComponentModel MCM;

void insert_elements(MCM &mcm, vector<double> elements) {
  vector<double>::iterator it;
  for(it=elements.begin(); it!=elements.end(); it++)
    mcm.insert_element(*it);
}

void remove_elements(MCM &mcm, vector<double> elements) {
  vector<double>::iterator it;
  for(it=elements.begin(); it!=elements.end(); it++)
    mcm.remove_element(*it);
}

int main() {
  cout << endl << "Begin:: test_multinomial_component_model" << endl;
  RandomNumberGenerator rng;

  // test settings
  int NUM_BUCKETS = 5;
  int num_values_to_test = 30;
  map<string, double> hypers;

  // generate all the random data to use
  //
  // initial parameters
  vector<double> dirichlet_alphas_to_test;
  dirichlet_alphas_to_test.push_back(0.5);
  dirichlet_alphas_to_test.push_back(1.0);
  dirichlet_alphas_to_test.push_back(10.0);
  //
  // elements to add
  vector<double> values_to_test;
  for(int i=0; i<num_values_to_test; i++) {
    int rand_i = rng.nexti(NUM_BUCKETS);
    values_to_test.push_back(rand_i);
  }
  //
  cout << "values_to_test: " << values_to_test << endl;
  vector<double> values_to_test_reversed = values_to_test;
  std::reverse(values_to_test_reversed.begin(), values_to_test_reversed.end());
  vector<double> values_to_test_shuffled = values_to_test;
  std::random_shuffle(values_to_test_shuffled.begin(), values_to_test_shuffled.end());

  // print generated values
  //
  cout << endl << "initial parameters: " << "\t";
  cout << "dirichlet_alphas_to_test: " << dirichlet_alphas_to_test << endl;
  cout << "values_to_test: " << values_to_test << endl;

  hypers["dirichlet_alpha"] = dirichlet_alphas_to_test[0];
  hypers["K"] = NUM_BUCKETS;
  MCM mcm(hypers);

  cout << "calc_marginal_logp() on empty MultinomialComponentModel: ";
  cout << mcm.calc_marginal_logp() << endl;
  //
  cout << "test insertion and removal in same order" << endl;
  insert_elements(mcm, values_to_test);
  cout << mcm << endl;
  remove_elements(mcm, values_to_test);
  cout << mcm << endl;
  //
  cout << "test insertion and removal in reversed order" << endl;
  insert_elements(mcm, values_to_test);
  cout << mcm << endl;
  remove_elements(mcm, values_to_test_reversed);
  cout << mcm << endl;
  //
  cout << "test insertion and removal in shuffled order" << endl;
  insert_elements(mcm, values_to_test);
  cout << mcm << endl;
  remove_elements(mcm, values_to_test_shuffled);
  cout << mcm << endl;


  cout << endl << "End:: test_multinomial_component_model" << endl;
}
